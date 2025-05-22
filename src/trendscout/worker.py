import time
import json
from sqlalchemy.orm import Session
from datetime import datetime

from trendscout.core.queue import queue_manager
from trendscout.core.logging import logger
from trendscout.db.session import SessionLocal
from trendscout.models.task import AgentTask
from trendscout.models.user import User # Ensure User model is imported
from trendscout.agents.trend_analyzer import TrendAnalyzerAgent
from trendscout.agents.content_generator import ContentGeneratorAgent
from trendscout.agents.scheduler import SchedulerAgent
from trendscout.agents.crew_defs import run_trend_to_post_workflow
from trendscout.core.config import get_settings # For potential future use

settings = get_settings()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_task(task_data: dict):
    task_id_from_queue = task_data.get("task_id") # This is the UUID string
    agent_type = task_data.get("agent_type")
    input_data = task_data.get("input_data", {})
    
    logger.info(f"Processing task {task_id_from_queue} of type {agent_type}")

    db_gen = get_db()
    db = next(db_gen)
    
    db_task = None  # Initialize db_task
    try:
        db_task = db.query(AgentTask).filter(AgentTask.task_id == task_id_from_queue).first()
        if not db_task:
            logger.error(f"Task {task_id_from_queue} not found in DB. Skipping.")
            return

        db_task.status = "running"
        db.commit()

        result_obj = None 
        error_message = None

        if agent_type == "trend_analyzer":
            agent = TrendAnalyzerAgent()
            query = input_data.get("query", "")
            logger.info(f"Running TrendAnalyzerAgent for task {task_id_from_queue} with query: '{query}'")
            result_obj = agent.run(query) 
        elif agent_type == "content_generator":
            agent = ContentGeneratorAgent()
            query = input_data.get("query", "")
            logger.info(f"Running ContentGeneratorAgent for task {task_id_from_queue} with query: '{query}'")
            result_obj = agent.run(query)
        elif agent_type == "scheduler":
            agent = SchedulerAgent()
            query = input_data.get("query", "")
            logger.info(f"Running SchedulerAgent for task {task_id_from_queue} with query: '{query}'")
            result_obj = agent.run(query)
        elif agent_type == "trend_to_post_crew":
            topic = input_data.get("topic")
            if topic:
                logger.info(f"Running Trend-to-Post Crew for task {task_id_from_queue} with topic: '{topic}'")
                result_obj = run_trend_to_post_workflow(topic) # This returns CrewOutput
            else:
                error_message = "Missing topic for trend_to_post_crew"
                logger.error(f"Task {task_id_from_queue}: {error_message}")
        else:
            error_message = f"Unknown agent type: {agent_type}"
            logger.error(f"Task {task_id_from_queue}: {error_message}")

        if error_message:
            db_task.status = "failed"
            db_task.error = error_message
            db_task.result = {"error": error_message} 
        else: 
            # Check if the agent/crew execution itself returned an error structure
            # (This part might need adjustment based on how agents/crews signal errors)
            if isinstance(result_obj, dict) and result_obj.get("error"): 
                db_task.status = "failed"
                db_task.error = result_obj.get("error")
                db_task.result = result_obj 
            else: 
                db_task.status = "completed"
                if agent_type == "trend_to_post_crew":
                    # 'result_obj' is a CrewOutput object here
                    serializable_result = {}
                    serializable_intermediate_steps = []

                    # Extract final output
                    if hasattr(result_obj, 'raw') and result_obj.raw is not None:
                        serializable_result['final_output'] = result_obj.raw
                    elif hasattr(result_obj, 'tasks_output') and result_obj.tasks_output and \
                         hasattr(result_obj.tasks_output[-1], 'raw_output'):
                        serializable_result['final_output'] = result_obj.tasks_output[-1].raw_output
                    elif hasattr(result_obj, 'json_output') and result_obj.json_output is not None: # CrewAI sometimes uses json_output
                        serializable_result['final_output'] = result_obj.json_output
                    elif hasattr(result_obj, 'pydantic_output') and result_obj.pydantic_output is not None: # Or pydantic_output
                        try:
                            serializable_result['final_output'] = result_obj.pydantic_output.model_dump_json()
                        except AttributeError: # If not a pydantic model, convert to string
                            serializable_result['final_output'] = str(result_obj.pydantic_output)
                    else:
                        # Fallback to string representation of the whole object if no specific output field is found
                        serializable_result['final_output'] = str(result_obj) 
                    
                    serializable_result['topic'] = input_data.get("topic", "N/A")

                    # Extract intermediate steps from tasks_output
                    if hasattr(result_obj, 'tasks_output') and result_obj.tasks_output:
                        for task_output_item in result_obj.tasks_output:
                            agent_name_str = "Unknown Agent"
                            # Try to get agent name/role from task_output_item
                            if hasattr(task_output_item, 'agent') and task_output_item.agent:
                                agent_name_str = str(task_output_item.agent) 
                            elif hasattr(task_output_item, 'task') and task_output_item.task and \
                                 hasattr(task_output_item.task, 'agent') and task_output_item.task.agent and \
                                 hasattr(task_output_item.task.agent, 'role'):
                                agent_name_str = task_output_item.task.agent.role
                            
                            step_output = task_output_item.raw_output if hasattr(task_output_item, 'raw_output') else str(task_output_item)
                            
                            timestamp_str = None
                            if hasattr(task_output_item, 'timestamp'):
                                if isinstance(task_output_item.timestamp, datetime):
                                    timestamp_str = task_output_item.timestamp.isoformat()
                                else:
                                    timestamp_str = str(task_output_item.timestamp)
                            
                            step = {
                                "agent_name": agent_name_str,
                                "output": step_output,
                                "timestamp": timestamp_str or datetime.utcnow().isoformat()
                            }
                            serializable_intermediate_steps.append(step)
                    
                    if hasattr(result_obj, 'usage_metrics') and result_obj.usage_metrics:
                        serializable_result['usage_metrics'] = result_obj.usage_metrics 
                    
                    db_task.result = serializable_result
                    db_task.intermediate_steps = serializable_intermediate_steps if serializable_intermediate_steps else None

                else: # For single agents
                    if isinstance(result_obj, (dict, list, str, int, float, bool)) or result_obj is None:
                        db_task.result = result_obj
                    else:
                        try:
                            # Attempt to get a dict representation
                            if hasattr(result_obj, 'model_dump'): # Pydantic models
                                db_task.result = result_obj.model_dump()
                            elif hasattr(result_obj, '__dict__'): # Standard objects
                                db_task.result = vars(result_obj)
                            else: # Fallback
                                db_task.result = {"output": str(result_obj)}
                        except Exception: # Catch any error during serialization attempt
                             db_task.result = {"output": str(result_obj)}
        
        db.commit()
        logger.info(f"Task {task_id_from_queue} finished with status: {db_task.status}")

    except Exception as e:
        logger.error(f"Error processing task {task_id_from_queue}: {e}", exc_info=True)
        if db_task: 
            db.rollback() 
            db_task.status = "failed"
            # Ensure error and result are serializable
            error_str = str(e)
            db_task.error = error_str
            try:
                # Attempt to serialize the exception args if they are simple
                db_task.result = {"error": error_str, "details": vars(e) if hasattr(e, '__dict__') else None}
            except TypeError:
                db_task.result = {"error": error_str}
            db.commit() 
    finally:
        db.close()


def main_worker_loop():
    logger.info("Starting Trendscout Worker...")
    # Define the order of queues to check, or a strategy
    # For now, we assume tasks are enqueued with their agent_type as queue_name
    # This means the worker needs to know all possible agent_types to listen to.
    # A more robust approach might be a single "tasks" queue, and agent_type is in task_data.
    # The current queue_manager.enqueue_task uses queue_name = agent_type.
    
    # Let's make the worker check all known queues.
    # This is not ideal for scaling but works for a simple setup.
    # A better way: one main queue, or worker per queue type.
    
    # For simplicity, let's assume the API enqueues to a generic 'tasks' queue
    # and the worker pulls from that. This requires changing tasks.py enqueue logic.
    # OR, the worker iterates through known agent_type queues.
    # The current `queue_manager.enqueue_task(task_in.agent_type, ...)` suggests
    # queues are named e.g. `queue:trend_analyzer`, `queue:trend_to_post_crew`.

    queues_to_monitor = [
        "trend_analyzer", 
        "content_generator", 
        "scheduler", 
        "trend_to_post_crew"
    ]

    while True:
        processed_a_task_this_cycle = False
        for queue_name in queues_to_monitor:
            # logger.debug(f"Checking queue: {queue_name}")
            task_data_json = queue_manager.redis_client.rpop(f"queue:{queue_name}") # Direct Redis call for simplicity here
            
            if task_data_json:
                try:
                    task_data = json.loads(task_data_json)
                    logger.info(f"Dequeued task from {queue_name}: {task_data.get('task_id')}")
                    process_task(task_data)
                    processed_a_task_this_cycle = True 
                    # If a task is processed, we can break and restart the loop
                    # to re-prioritize or just continue checking other queues.
                    # For now, let's continue to ensure all queues get a chance.
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode task data from {queue_name}: {task_data_json}")
                except Exception as e:
                    logger.error(f"Unexpected error processing task from {queue_name}: {e}", exc_info=True)
            # else:
                # logger.debug(f"Queue {queue_name} is empty.")
        
        if not processed_a_task_this_cycle:
            # logger.debug("All monitored queues empty. Sleeping...")
            time.sleep(settings.OLLAMA_TIMEOUT / 100 if settings.OLLAMA_TIMEOUT > 100 else 5) # Sleep if no tasks found, e.g., 5 seconds

if __name__ == "__main__":
    # This allows running the worker directly for development/testing
    # In production, this script would be run by the worker service in Docker
    main_worker_loop()
