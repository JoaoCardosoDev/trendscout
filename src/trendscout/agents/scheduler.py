import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from crewai import Task

from .base import BaseAgent

SUPPORTED_PLATFORMS: Set[str] = {"twitter", "reddit", "instagram", "linkedin", "blog"}


class SchedulerAgent(BaseAgent):
    """Agent responsible for determining optimal content publishing schedules."""

    def __init__(self, model_name: Optional[str] = None):
        super().__init__(
            name="Scheduler Agent",  # Ensured "Agent" is part of the name for consistency with test
            role="Scheduling Optimization Expert",
            goal="Determine optimal publishing times for content across platforms",
            backstory="Analytics expert specializing in content scheduling optimization, "
            "with deep understanding of platform-specific engagement patterns "
            "and audience behavior across different time zones.",
            temperature=0.6,
            model_name=model_name,
        )

    def get_agent_config(self) -> Dict[str, str]:
        """Returns the agent's configuration."""
        return {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
        }

    def get_optimal_time(
        self,
        content_data: Dict[str, Any],
        platform: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Determines the optimal publishing time for given content.

        Args:
            content_data: Dictionary containing content details (e.g., title, target_audience).
            platform: Optional target platform.
            timezone: Optional target timezone.

        Returns:
            A dictionary containing the scheduling recommendations.

        Raises:
            ValueError: If input validation fails or the scheduling response is invalid.
        """
        if not content_data or not content_data.get("title"):
            raise ValueError("Content data must contain at least a title.")

        if platform and platform.lower() not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported platform: {platform}. Supported platforms are: {', '.join(SUPPORTED_PLATFORMS)}"
            )

        if timezone and not isinstance(timezone, str):  # Basic check, can be improved
            raise ValueError("Invalid timezone format. Timezone should be a string.")

        # Construct prompt for the LLM
        prompt_parts = [
            "Analyze the provided content data to determine the optimal publishing time.",
            f"Content Title: {content_data['title']}",
        ]
        if "target_audience" in content_data:
            prompt_parts.append(f"Target Audience: {content_data['target_audience']}")
        if "content_type" in content_data:
            prompt_parts.append(f"Content Type: {content_data['content_type']}")

        if platform:
            prompt_parts.append(f"Target Platform: {platform}")
        if timezone:
            prompt_parts.append(f"Preferred Timezone: {timezone}")

        prompt_parts.append(
            '\nReturn the schedule as a JSON object with a root key "schedule" containing '
            '"recommended_time" (ISO 8601 format), "timezone" (string, e.g., UTC), '
            '"predicted_engagement" (float), "reasoning" (string), '
            'and "alternative_times" (list of ISO 8601 strings).'
        )
        prompt_parts.append(
            "Example JSON format:\n"
            """{
                "schedule": {
                    "recommended_time": "2025-05-15T14:30:00Z",
                    "timezone": "UTC",
                    "predicted_engagement": 0.85,
                    "reasoning": "High user activity observed during this timeframe.",
                    "alternative_times": [
                        "2025-05-15T18:30:00Z",
                        "2025-05-16T09:30:00Z"
                    ]
                }
            }"""
        )

        description = "\n".join(prompt_parts)

        task = Task(
            description=description,
            agent=self.agent,
            expected_output="A JSON string representing the optimal schedule.",
        )

        raw_result = self.agent.execute_task(task=task)

        try:
            parsed_result = json.loads(raw_result)
            if not isinstance(parsed_result, dict) or "schedule" not in parsed_result:
                raise ValueError("Parsed JSON is not a dict or missing 'schedule' key.")
            # Further validation of inner structure could be added here if needed
            return parsed_result
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid scheduling response format: Failed to decode JSON. Error: {e}. Raw response: {raw_result}"
            )
        except ValueError as e:  # Catch specific ValueError from structure check
            raise ValueError(
                f"Invalid scheduling response format: {e}. Raw response: {raw_result}"
            )

    def run(self, query: str) -> Dict[str, Any]:
        """
        Synchronous method to generate a schedule based on a simple query string (content description/campaign).
        This adapts the simple query to the agent's expected input for its underlying CrewAI agent.
        """

        prompt = f"""
        As a Scheduling Optimization Expert, create an optimal publishing schedule for the following content or campaign:

        Content/Campaign Description: "{query}"

        Consider target platforms (e.g., Twitter, Instagram, Blog), target audience, and general best practices for engagement.

        Provide:
        1. A detailed publishing schedule with suggested timings.
        2. Rationale for your scheduling decisions.
        3. Optimization recommendations.

        Format the response as a structured output.
        """

        # Execute scheduling using the underlying CrewAI agent
        task = Task(
            description=prompt.strip(),
            agent=self.agent,
            expected_output="A structured publishing schedule, rationale for decisions, and optimization recommendations.",
        )
        raw_result = self.agent.execute_task(task)

        # Parse and structure the result
        structured_result = self._parse_result(
            raw_result
        )  # _parse_result might need adjustment

        return structured_result

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous method to generate optimal publishing schedule for content based on structured input.

        Args:
            data: Dictionary containing content and scheduling requirements
                 Expected format:
                 {
                     "content_ideas": List[Dict],  # Content from ContentGenerator
                     "platform": str,  # Target platform
                     "timezone": str,  # Target timezone
                     "constraints": Dict[str, Any],  # Scheduling constraints
                     "performance_data": Dict[str, Any]  # Optional historical data
                 }

        Returns:
            Dict containing scheduling recommendations:
            {
                "schedule": List[Dict],  # Scheduled content items
                "rationale": str,  # Explanation of scheduling decisions
                "optimizations": List[str],  # Optimization recommendations
                "metrics": Dict[str, Any]  # Expected performance metrics
            }
        """
        # Validate input data
        if not self._validate_input(data):
            raise ValueError("Invalid input data format")

        # Create prompt for schedule optimization
        prompt = self._create_scheduling_prompt(data)

        task = Task(  # Create a Task object
            description=prompt,
            agent=self.agent,
            expected_output="A structured response with schedule, rationale, optimizations, and metrics.",
        )
        # Generate schedule using CrewAI agent
        result = await self.agent.execute_task_async(task=task)  # Use async execution

        # Parse and structure the result
        structured_result = self._parse_result(result)

        return structured_result

    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate the scheduling recommendations.

        Args:
            result: The scheduling result to validate

        Returns:
            bool: True if result is valid, False otherwise
        """
        required_keys = {"schedule", "rationale", "optimizations", "metrics"}

        # Check for required keys
        if not all(key in result for key in required_keys):
            return False

        # Validate schedule structure
        if not isinstance(result["schedule"], list) or not result["schedule"]:
            return False

        # Validate schedule items
        for item in result["schedule"]:
            if not all(
                key in item
                for key in {"content_id", "publish_time", "expected_engagement"}
            ):
                return False

        # Validate rationale
        if not isinstance(result["rationale"], str) or not result["rationale"].strip():
            return False

        # Validate optimizations
        if not isinstance(result["optimizations"], list) or not result["optimizations"]:
            return False

        return True

    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data format for the execute method."""
        required_keys = {"content_ideas", "platform", "timezone", "constraints"}

        if not all(key in data for key in required_keys):
            return False

        if not isinstance(data["content_ideas"], list) or not data["content_ideas"]:
            return False

        # Validate platform is supported
        if data["platform"].lower() not in SUPPORTED_PLATFORMS:
            return False

        # Basic timezone format validation
        if not isinstance(data["timezone"], str) or not data["timezone"].strip():
            return False

        # Validate constraints
        if not isinstance(data["constraints"], dict):
            return False

        return True

    def _create_scheduling_prompt(self, data: Dict[str, Any]) -> str:
        """Create a detailed prompt for schedule optimization for the execute method."""
        content_count = len(data["content_ideas"])
        constraints_str = (
            "\n".join([f"- {k}: {v}" for k, v in data["constraints"].items()])
            if data["constraints"]
            else "None"
        )

        prompt = f"""
        As a Scheduling Optimization Expert, create an optimal publishing schedule for:

        Platform: {data["platform"]}
        Timezone: {data["timezone"]}
        Content Items: {content_count}

        Constraints:
        {constraints_str}

        Consider:
        1. Platform-specific peak engagement times
        2. Target audience activity patterns
        3. Content type and seasonality
        4. Frequency and spacing of posts
        5. Competition and noise levels
        6. Time zone impact on reach

        Provide:
        1. A detailed publishing schedule with timing and expected engagement for each content item.
        2. Rationale for scheduling decisions.
        3. Optimization recommendations.
        4. Expected performance metrics.

        Format the response as a structured output that can be parsed into schedule, rationale, optimizations, and metrics,
        as handled by the internal _parse_result method.
        Example of how _parse_result expects sections:
        Section 1 (Schedule):
        - content_id_1 - YYYY-MM-DDTHH:MM:SSZ - 0.75
        - content_id_2 - YYYY-MM-DDTHH:MM:SSZ - 0.80

        Section 2 (Rationale):
        Detailed explanation...

        Section 3 (Optimizations):
        - Recommendation 1
        - Recommendation 2

        Section 4 (Metrics):
        MetricName1: Value1
        MetricName2: Value2
        """

        return prompt.strip()

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """Parse and structure the AI model's response for the execute method."""
        try:
            # Split the content into sections based on double newlines
            # This assumes the LLM will follow the multi-section format.
            sections = result.strip().split("\n\n")

            parsed_data: Dict[str, Any] = {
                "schedule": [],
                "rationale": "",
                "optimizations": [],
                "metrics": {},
            }

            if not sections:
                raise ValueError(
                    "Result string is empty or not formatted into sections."
                )

            # Section 1: Schedule
            # Expected format: "- content_id - publish_time - expected_engagement"
            if len(sections) > 0:
                schedule_lines = sections[0].split("\n")
                for line in schedule_lines:
                    line = line.strip()
                    if line.startswith("- "):
                        parts = [p.strip() for p in line[2:].split(" - ")]
                        if len(parts) == 3:
                            parsed_data["schedule"].append(
                                {
                                    "content_id": parts[0],
                                    "publish_time": parts[1],
                                    "expected_engagement": parts[
                                        2
                                    ],  # Keep as string, convert later if needed
                                }
                            )

            # Section 2: Rationale
            if len(sections) > 1:
                parsed_data["rationale"] = sections[1].strip()

            # Section 3: Optimizations
            # Expected format: "- Recommendation"
            if len(sections) > 2:
                optimization_lines = sections[2].split("\n")
                for line in optimization_lines:
                    line = line.strip()
                    if line.startswith("- "):
                        parsed_data["optimizations"].append(line[2:].strip())

            # Section 4: Metrics
            # Expected format: "MetricName: Value"
            if len(sections) > 3:
                metric_lines = sections[3].split("\n")
                for line in metric_lines:
                    line = line.strip()
                    if ":" in line:
                        key, value = line.split(":", 1)
                        parsed_data["metrics"][key.strip()] = value.strip()

            if (
                not parsed_data["schedule"]
                and not parsed_data["rationale"]
                and not parsed_data["optimizations"]
                and not parsed_data["metrics"]
            ):
                # If all fields are empty, it's likely a parsing failure or unexpected format.
                raise ValueError("Failed to parse any meaningful data from the result.")

            return parsed_data

        except Exception as e:
            # Fallback structure if parsing fails
            current_time = datetime.now()
            return {
                "schedule": [
                    {
                        "content_id": "error",
                        "publish_time": (current_time + timedelta(hours=1)).isoformat(),
                        "expected_engagement": "Error parsing schedule",
                    }
                ],
                "rationale": f"Error parsing schedule: {str(e)}. Raw result: {result}",
                "optimizations": ["Review raw scheduling output"],
                "metrics": {"error": "Failed to parse metrics"},
            }
