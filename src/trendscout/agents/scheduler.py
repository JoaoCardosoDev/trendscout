from typing import Any, Dict
from datetime import datetime, timedelta
from crewai import Task  # Import Task
from .base import BaseAgent


class SchedulerAgent(BaseAgent):
    """Agent responsible for determining optimal content publishing schedules."""

    def __init__(self):
        super().__init__(
            name="Scheduler",
            role="Scheduling Optimization Expert",
            goal="Determine optimal publishing times for content across platforms",
            backstory="Analytics expert specializing in content scheduling optimization, "
            "with deep understanding of platform-specific engagement patterns "
            "and audience behavior across different time zones.",
            temperature=0.6,
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

        # Generate schedule using CrewAI agent
        result = await self.agent.execute_task(prompt)

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
        """Validate input data format."""
        required_keys = {"content_ideas", "platform", "timezone", "constraints"}

        if not all(key in data for key in required_keys):
            return False

        if not isinstance(data["content_ideas"], list) or not data["content_ideas"]:
            return False

        # Validate platform is supported
        if data["platform"].lower() not in {
            "twitter",
            "reddit",
            "instagram",
            "linkedin",
        }:
            return False

        # Basic timezone format validation
        if not isinstance(data["timezone"], str) or not data["timezone"].strip():
            return False

        # Validate constraints
        if not isinstance(data["constraints"], dict):
            return False

        return True

    def _create_scheduling_prompt(self, data: Dict[str, Any]) -> str:
        """Create a detailed prompt for schedule optimization."""
        content_count = len(data["content_ideas"])
        constraints = "\n".join([f"- {k}: {v}" for k, v in data["constraints"].items()])

        prompt = f"""
        As a Scheduling Optimization Expert, create an optimal publishing schedule for:

        Platform: {data["platform"]}
        Timezone: {data["timezone"]}
        Content Items: {content_count}

        Constraints:
        {constraints}

        Consider:
        1. Platform-specific peak engagement times
        2. Target audience activity patterns
        3. Content type and seasonality
        4. Frequency and spacing of posts
        5. Competition and noise levels
        6. Time zone impact on reach

        Provide:
        1. A detailed publishing schedule with timing and expected engagement
        2. Rationale for scheduling decisions
        3. Optimization recommendations
        4. Expected performance metrics

        Format the response as a structured output that can be parsed into schedule, rationale, optimizations, and metrics.
        """

        return prompt.strip()

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """Parse and structure the AI model's response."""
        try:
            # Split the content into sections
            sections = result.split("\n\n")

            # Extract schedule (assuming first section)
            schedule = []
            for line in sections[0].split("\n"):
                if line.strip().startswith("- "):
                    parts = line.strip().split(" - ")
                    if len(parts) >= 3:
                        schedule.append(
                            {
                                "content_id": parts[0].strip("- "),
                                "publish_time": parts[1],
                                "expected_engagement": parts[2],
                            }
                        )

            # Extract rationale (assuming second section)
            rationale = sections[1] if len(sections) > 1 else ""

            # Extract optimizations (assuming third section)
            optimizations = [
                line.strip().split("- ")[1]
                for line in (sections[2].split("\n") if len(sections) > 2 else [])
                if line.strip().startswith("- ")
            ]

            # Extract metrics (assuming fourth section)
            metrics = {}
            if len(sections) > 3:
                for line in sections[3].split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metrics[key.strip()] = value.strip()

            return {
                "schedule": schedule,
                "rationale": rationale,
                "optimizations": optimizations,
                "metrics": metrics,
            }

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
                "rationale": f"Error parsing schedule: {str(e)}",
                "optimizations": ["Review raw scheduling output"],
                "metrics": {"error": "Failed to parse metrics"},
            }
