from typing import Any, Dict
from crewai import Task  # Import Task
from .base import BaseAgent


class TrendAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing and identifying trending topics."""

    def __init__(self):
        super().__init__(
            name="Trend Analyzer",
            role="Trend Analysis Expert",
            goal="Identify and analyze trending topics from social media data",
            backstory="Expert at pattern recognition and trend identification, "
            "specializing in social media content analysis and discovering "
            "emerging trends across platforms.",
            temperature=0.7,  # Balanced between creativity and accuracy
        )

    def run(self, query: str) -> Dict[str, Any]:
        """
        Synchronous method to run trend analysis based on a simple query string.
        This adapts the simple query to the agent's expected input for its underlying CrewAI agent.
        """

        prompt = f"""
        Analyze the following topic or query to identify current trends, key insights, and potential content angles:
        Query: "{query}"

        Provide:
        1. A list of identified trends related to the query.
        2. Detailed analysis of each trend.
        3. Actionable recommendations or content ideas based on these findings.

        Format the response as a structured analysis.
        """

        # Execute analysis using the underlying CrewAI agent
        # BaseAgent's self.agent is a CrewAI Agent instance
        task = Task(
            description=prompt.strip(),
            agent=self.agent,
            expected_output="A structured analysis including trends, detailed analysis, and actionable recommendations.",
        )
        raw_result = self.agent.execute_task(task)

        # Parse and structure the result (can reuse or adapt _parse_result)
        # For simplicity, let's assume _parse_result can handle this raw_result.
        structured_result = self._parse_result(raw_result)

        return structured_result

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous method to execute trend analysis on provided structured social media data.

        Args:
            data: Dictionary containing social media data to analyze
                 Expected format:
                 {
                     "platform": str,  # e.g., "twitter", "reddit"
                     "content": List[Dict],  # List of posts/tweets
                     "timeframe": str,  # e.g., "24h", "7d"
                 }

        Returns:
            Dict containing identified trends and their analysis:
            {
                "trends": List[Dict],  # List of identified trends
                "analysis": str,  # Detailed analysis of trends
                "recommendations": List[str]  # Action recommendations
            }
        """
        # Validate input data
        if not self._validate_input(data):
            raise ValueError("Invalid input data format")

        # Create prompt for the AI model
        prompt = self._create_analysis_prompt(data)

        # Execute analysis using CrewAI agent
        result = await self.agent.execute_task(prompt)

        # Parse and structure the result
        structured_result = self._parse_result(result)

        return structured_result

    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate the analysis result.

        Args:
            result: The analysis result to validate

        Returns:
            bool: True if result is valid, False otherwise
        """
        required_keys = {"trends", "analysis", "recommendations"}

        # Check for required keys
        if not all(key in result for key in required_keys):
            return False

        # Validate trends structure
        if not isinstance(result["trends"], list) or not result["trends"]:
            return False

        # Validate analysis content
        if not isinstance(result["analysis"], str) or not result["analysis"].strip():
            return False

        # Validate recommendations
        if (
            not isinstance(result["recommendations"], list)
            or not result["recommendations"]
        ):
            return False

        return True

    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data format."""
        required_keys = {"platform", "content", "timeframe"}

        if not all(key in data for key in required_keys):
            return False

        if not isinstance(data["content"], list):
            return False

        if data["platform"].lower() not in {"twitter", "reddit"}:
            return False

        return True

    def _create_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create a detailed prompt for trend analysis."""
        platform = data["platform"]
        timeframe = data["timeframe"]
        content_count = len(data["content"])

        prompt = f"""
        As a Trend Analysis Expert, analyze the following {platform} data from the past {timeframe}:

        Dataset: {content_count} posts/tweets

        Identify:
        1. Key trending topics and themes
        2. Emerging patterns in engagement
        3. Sentiment trends
        4. Notable discussions or conversations
        5. Potential viral content indicators

        Provide:
        1. A list of identified trends with supporting data
        2. Detailed analysis of each trend
        3. Actionable recommendations based on findings

        Format the response as a structured analysis that can be parsed into trends, analysis, and recommendations.
        """

        return prompt.strip()

    def _parse_result(self, result: str) -> Dict[str, Any]:
        """Parse and structure the AI model's response."""
        try:
            # Basic structure assuming model returns somewhat formatted text
            sections = result.split("\n\n")

            # Extract trends (assuming first section contains trends)
            trends = [
                {"topic": line.strip().split(": ")[1]}
                for line in sections[0].split("\n")
                if line.strip().startswith("- ")
            ]

            # Extract analysis (assuming middle sections)
            analysis = "\n".join(sections[1:-1])

            # Extract recommendations (assuming last section)
            recommendations = [
                line.strip().split("- ")[1]
                for line in sections[-1].split("\n")
                if line.strip().startswith("- ")
            ]

            return {
                "trends": trends,
                "analysis": analysis,
                "recommendations": recommendations,
            }

        except Exception as e:
            # Fallback structure if parsing fails
            return {
                "trends": [{"topic": "Error parsing trends"}],
                "analysis": "Error parsing analysis: " + str(e),
                "recommendations": ["Review raw analysis output"],
            }
