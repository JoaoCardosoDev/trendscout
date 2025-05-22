document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const taskForm = document.getElementById('task-form');
    const loginSection = document.getElementById('login-section');
    const taskSection = document.getElementById('task-section');
    const loginMessage = document.getElementById('login-message');
    const taskCreationMessage = document.getElementById('task-creation-message');
    const taskStatusArea = document.getElementById('task-status-area');

    let accessToken = localStorage.getItem('accessToken');
    let activeTasks = {}; // To store interval IDs for polling

    const API_BASE_URL = ''; // Assuming served from the same origin

    function showMessage(element, message, isError = false) {
        element.textContent = message;
        element.className = 'message ' + (isError ? 'error' : 'success');
        element.style.display = 'block';
    }

    function hideMessage(element) {
        element.style.display = 'none';
        element.textContent = '';
    }

    function updateUIVisibility() {
        if (accessToken) {
            loginSection.style.display = 'none';
            taskSection.style.display = 'block';
            // Check if task area is empty and add no tasks message
            if (!taskStatusArea.querySelector('.task-item') && !document.getElementById('no-tasks-message')) {
                taskStatusArea.innerHTML = '<p id="no-tasks-message">No tasks created or being tracked yet.</p>';
            }
        } else {
            loginSection.style.display = 'block';
            taskSection.style.display = 'none';
            taskStatusArea.innerHTML = '<p id="no-tasks-message">Please log in to create and view tasks.</p>'; // Message for logged out state
            activeTasks = {}; // Clear active polling on logout
        }
    }

    updateUIVisibility();

    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        hideMessage(loginMessage);

        const formData = new FormData(loginForm);
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Login failed with status: ${response.status}`);
            }

            const data = await response.json();
            accessToken = data.access_token;
            localStorage.setItem('accessToken', accessToken);
            showMessage(loginMessage, 'Login successful!', false);
            updateUIVisibility();
        } catch (error) {
            showMessage(loginMessage, `Login error: ${error.message}`, true);
            console.error('Login error:', error);
        }
    });

    taskForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        hideMessage(taskCreationMessage);

        if (!accessToken) {
            showMessage(taskCreationMessage, 'You must be logged in to create tasks.', true);
            return;
        }

        const taskType = document.getElementById('task-type').value;
        const inputDataValue = document.getElementById('task-input').value;
        
        let payload;
        if (taskType === "trend_to_post_crew") {
            payload = {
                agent_type: taskType,
                input_data: { topic: inputDataValue }
            };
        } else {
            payload = {
                agent_type: taskType,
                input_data: { query: inputDataValue } 
            };
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/tasks/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                let errorMsg = `Task creation failed: ${response.status}`;
                try {
                    const errorData = await response.json();
                    if (errorData.detail) {
                        if (typeof errorData.detail === 'string') {
                            errorMsg = errorData.detail;
                        } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0 && errorData.detail[0].msg) {
                            // Handle Pydantic validation errors
                            errorMsg = errorData.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
                        } else {
                            errorMsg = JSON.stringify(errorData.detail);
                        }
                    }
                } catch (e) {
                    // If parsing errorData fails, stick with the status code
                }
                throw new Error(errorMsg);
            }

            const task = await response.json();
            showMessage(taskCreationMessage, `Task created successfully! ID: ${task.task_id}`, false);
            displayTaskStatus(task);
            pollTaskStatus(task.task_id);

        } catch (error) {
            showMessage(taskCreationMessage, `Task creation error: ${error.message}`, true);
            console.error('Task creation error:', error);
        }
    });

    function displayTaskStatus(task) {
        const noTasksMsg = document.getElementById('no-tasks-message');
        if (noTasksMsg) {
            noTasksMsg.remove();
        }

        let taskDiv = document.getElementById(`task-${task.task_id}`);
        if (!taskDiv) {
            taskDiv = document.createElement('div');
            taskDiv.id = `task-${task.task_id}`;
            taskDiv.className = 'task-item';
            taskStatusArea.appendChild(taskDiv);
        }

        let formattedInputHtml = 'N/A';
        if (task.input_data !== null && typeof task.input_data !== 'undefined') {
            if (typeof task.input_data === 'object') {
                formattedInputHtml = `<pre>${JSON.stringify(task.input_data, null, 2)}</pre>`;
            } else {
                formattedInputHtml = `<pre>${String(task.input_data)}</pre>`;
            }
        }

        let formattedResultHtml = 'Pending...';
        if (task.result !== null && typeof task.result !== 'undefined') {
            if (typeof task.result === 'object') {
                formattedResultHtml = `<pre>${JSON.stringify(task.result, null, 2)}</pre>`;
            } else {
                formattedResultHtml = `<pre>${String(task.result)}</pre>`;
            }
        }

        taskDiv.innerHTML = `
            <p><strong>Task ID:</strong> ${task.task_id}</p>
            <p><strong>Agent Type:</strong> ${task.agent_type}</p>
            <p><strong>Status:</strong> ${task.status}</p>
            <p><strong>Created:</strong> ${new Date(task.created_at).toLocaleString()}</p>
            <p><strong>Input:</strong></p>
            <div class="task-input-content">${formattedInputHtml}</div>
            <p><strong>Result:</strong></p>
            <div class="task-result-content">${formattedResultHtml}</div>
            <p><strong>Error:</strong> ${task.error ? task.error : 'None'}</p>
            <div class="intermediate-steps-container" id="task-${task.task_id}-intermediate-steps"></div>
        `;

        const intermediateStepsContainer = taskDiv.querySelector(`#task-${task.task_id}-intermediate-steps`);
        intermediateStepsContainer.innerHTML = '';

        if (task.agent_type === 'trend_to_post_crew' && task.intermediate_steps && Array.isArray(task.intermediate_steps) && task.intermediate_steps.length > 0) {
            const stepsTitle = document.createElement('h4');
            stepsTitle.textContent = 'Intermediate Steps:';
            intermediateStepsContainer.appendChild(stepsTitle);

            const stepsList = document.createElement('ul');
            stepsList.className = 'intermediate-steps-list';

            task.intermediate_steps.forEach(step => {
                const stepItem = document.createElement('li');
                stepItem.className = 'intermediate-step-item';
                
                let stepOutput = step.output;
                // Attempt to parse output if it's a JSON string
                try {
                    const parsedOutput = JSON.parse(step.output);
                    // If parsing is successful and it's an object/array, pretty print it
                    if (typeof parsedOutput === 'object' && parsedOutput !== null) {
                        stepOutput = JSON.stringify(parsedOutput, null, 2);
                        stepOutput = `<pre>${stepOutput}</pre>`; // Use pre for formatting
                    } else {
                        // If it's a simple type (string, number, boolean) after parsing, just use it
                        // Or if it was a string that just happened to be valid JSON (e.g. "\"a simple string\"")
                        stepOutput = `<pre>${step.output}</pre>`;
                    }
                } catch (e) {
                    // If output is not a valid JSON string, display as is, wrapped in pre
                    stepOutput = `<pre>${step.output}</pre>`;
                }

                stepItem.innerHTML = `
                    <p><strong>Agent:</strong> ${step.agent || 'N/A'}</p>
                    <p><strong>Task:</strong> ${step.task_description || 'N/A'}</p>
                    <div><strong>Output:</strong> ${stepOutput}</div>
                `;
                stepsList.appendChild(stepItem);
            });
            intermediateStepsContainer.appendChild(stepsList);
        }
    }

    async function fetchTaskStatus(taskId) {
        if (!accessToken) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (!response.ok) {
                console.error(`Failed to fetch status for task ${taskId}: ${response.status}`);
                return null;
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching status for task ${taskId}:`, error);
            return null;
        }
    }

    function pollTaskStatus(taskId) {
        if (activeTasks[taskId]) {
            clearInterval(activeTasks[taskId]);
        }

        activeTasks[taskId] = setInterval(async () => {
            const task = await fetchTaskStatus(taskId);
            if (task) {
                displayTaskStatus(task);
                if (task.status === 'completed' || task.status === 'failed' || task.status === 'error') {
                    clearInterval(activeTasks[taskId]);
                    delete activeTasks[taskId];
                }
            } else {
                // Optional: Stop polling if fetching status fails consistently
            }
        }, 5000);
    }

    const logoutButton = document.createElement('button');
    logoutButton.textContent = 'Logout';
    logoutButton.id = 'logout-button';
    logoutButton.onclick = () => {
        accessToken = null;
        localStorage.removeItem('accessToken');
        for (const taskId in activeTasks) {
            clearInterval(activeTasks[taskId]);
        }
        activeTasks = {};
        updateUIVisibility();
        hideMessage(loginMessage);
        hideMessage(taskCreationMessage);
    };
    taskSection.appendChild(logoutButton);
});
