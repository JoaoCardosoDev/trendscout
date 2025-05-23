import json
from typing import Any, Dict, List, Optional, Set

from crewai import Task

from .base import BaseAgent

SUPPORTED_PLATFORMS_TA: Set[str] = {
    "twitter",
    "reddit",
    "instagram",
    "linkedin",
    "news_api",
    "google_trends",
}


class TrendAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing and identifying trending topics."""

    def __init__(self, model: Optional[str] = None):
        super().__init__(
            name="Trend Analyzer Agent",  # Ensured "Agent" is part of the name
            role="Trend Analysis Expert",
            goal="Identify and analyze trending topics from social media data and other sources",
            backstory="Expert at pattern recognition and trend identification, "
            "specializing in social media content analysis, news aggregation, and discovering "
            "emerging trends across various platforms and data streams.",
            temperature=0.7,
            model_name=model,  # Pass model to super's model_name
        )
        self.model = model  # Store for test verification if needed

    def get_agent_config(self) -> Dict[str, str]:
        """Returns the agent's configuration."""
        return {
            "name": self.name,
            "role": self.role,
            "goal": self.goal,
            "backstory": self.backstory,
        }

    def analyze_trends(
        self,
        platforms: List[str],
        timeframe: Optional[str] = "last_24_hours",
        keywords: Optional[List[str]] = None,
        region: Optional[str] = None,  # Added region as per common use cases
        language: Optional[str] = None,  # Added language
    ) -> Dict[str, Any]:
        """
        Analyzes trends based on specified platforms, timeframe, keywords, etc.

        Args:
            platforms: List of platforms to analyze (e.g., ["Twitter", "Reddit"]).
            timeframe: Timeframe for analysis (e.g., "last_24_hours", "last_week").
            keywords: Optional list of keywords to focus on.
            region: Optional region for trend localization.
            language: Optional language for filtering content.

        Returns:
            A dictionary containing the trend analysis results.

        Raises:
            ValueError: If input validation fails or the analysis response is invalid.
        """
        if not platforms:
            raise ValueError("At least one platform must be specified.")

        for p in platforms:
            if p.lower() not in SUPPORTED_PLATFORMS_TA:
                raise ValueError(
                    f"Unsupported platform: {p}. Supported platforms are: {', '.join(SUPPORTED_PLATFORMS_TA)}"
                )

        # Construct prompt for the LLM
        prompt_parts = [
            "As a Trend Analysis Expert, analyze trends based on the following criteria:",
            f"Platforms: {', '.join(platforms)}",
            f"Timeframe: {timeframe}",
        ]
        if keywords:
            prompt_parts.append(f"Keywords: {', '.join(keywords)}")
        if region:
            prompt_parts.append(f"Region: {region}")
        if language:
            prompt_parts.append(f"Language: {language}")

        prompt_parts.append(
            "\nIdentify key trends, their sentiment, popularity, and supporting sources."
        )
        prompt_parts.append(
            'Return the analysis as a JSON object with a root key "trends" which is a list of objects. '
            'Each trend object should contain "topic" (string), "sentiment" (string, e.g., positive/negative/neutral), '
            '"popularity" (float, 0.0 to 1.0), and "sources" (list of strings).'
        )
        prompt_parts.append(
            "Example JSON format:\n"
            """{
                "trends": [
                    {
                        "topic": "AI in Healthcare",
                        "sentiment": "positive",
                        "popularity": 0.9,
                        "sources": ["Twitter", "News Articles"]
                    },
                    {
                        "topic": "Remote Work Tools",
                        "sentiment": "neutral",
                        "popularity": 0.75,
                        "sources": ["Reddit", "LinkedIn"]
                    }
                ]
            }"""
        )

        description = "\n".join(prompt_parts)

        task = Task(
            description=description,
            agent=self.agent,
            expected_output="A JSON string representing the trend analysis.",
        )

        raw_result = self.agent.execute_task(task=task)

        try:
            parsed_result = json.loads(raw_result)
            if not isinstance(parsed_result, dict) or "trends" not in parsed_result:
                raise ValueError("Parsed JSON is not a dict or missing 'trends' key.")
            if not isinstance(parsed_result["trends"], list):
                raise ValueError("'trends' key must be a list.")
            # Further validation of inner structure could be added here
            return parsed_result
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid analysis response format: Failed to decode JSON. Error: {e}. Raw response: {raw_result}"
            )
        except ValueError as e:  # Catch specific ValueError from structure check
            raise ValueError(
                f"Invalid analysis response format: {e}. Raw response: {raw_result}"
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

        task = Task(
            description=prompt.strip(),
            agent=self.agent,
            expected_output="A structured analysis including trends, detailed analysis, and actionable recommendations.",
        )
        raw_result = self.agent.execute_task(task)

        # For run, we might need a different parser or adapt _parse_result_generic
        # This is a placeholder, assuming a generic parsing might work or needs specific implementation.
        return self._parse_generic_result(raw_result)

    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous method to execute trend analysis on provided structured social media data.
        This method is kept for compatibility but `analyze_trends` is the primary method for tests.

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
        if not self._validate_input_execute(data):
            raise ValueError("Invalid input data format for execute method.")

        prompt = self._create_analysis_prompt_execute(data)

        task = Task(
            description=prompt,
            agent=self.agent,
            expected_output="A structured analysis with trends, analysis, and recommendations.",
        )
        result = await self.agent.execute_task_async(task=task)
        return self._parse_result_execute(result)

    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate the analysis result from the execute method.
        """
        required_keys = {"trends", "analysis", "recommendations"}
        if not all(key in result for key in required_keys):
            return False
        if not isinstance(result["trends"], list) or not result["trends"]:
            return False
        if not isinstance(result["analysis"], str) or not result["analysis"].strip():
            return False
        if (
            not isinstance(result["recommendations"], list)
            or not result["recommendations"]
        ):
            return False
        return True

    def _validate_input_execute(self, data: Dict[str, Any]) -> bool:
        """Validate input data format for the execute method."""
        required_keys = {"platform", "content", "timeframe"}
        if not all(key in data for key in required_keys):
            return False
        if not isinstance(data["content"], list):
            return False
        if data["platform"].lower() not in {"twitter", "reddit"}:
            return False  # Simplified for execute
        return True

    def _create_analysis_prompt_execute(self, data: Dict[str, Any]) -> str:
        """Create a detailed prompt for trend analysis for the execute method."""
        platform = data["platform"]
        timeframe = data["timeframe"]
        content_count = len(data["content"])

        return f"""
        As a Trend Analysis Expert, analyze the following {platform} data from the past {timeframe}:
        Dataset: {content_count} posts/tweets.
        Identify: Key trending topics, engagement patterns, sentiment, discussions, viral indicators.
        Provide: List of trends, detailed analysis, actionable recommendations.
        Format: Structured analysis for trends, analysis, recommendations sections.
        """.strip()

    def _parse_result_execute(self, result: str) -> Dict[str, Any]:
        """Parse and structure the AI model's response for the execute method."""
        try:
            sections = result.strip().split("\n\n")
            trends = []
            analysis = ""
            recommendations = []

            # This is a simplified parser, assumes specific formatting from LLM for execute method
            if len(sections) > 0:  # Trends
                trends_lines = sections[0].split("\n")
                for line in trends_lines:
                    if line.strip().startswith("- "):
                        topic_part = line.strip()[2:]  # Remove "- "
                        # Basic parsing, might need refinement based on actual LLM output
                        trends.append(
                            {
                                "topic": (
                                    topic_part.split(":")[0].strip()
                                    if ":" in topic_part
                                    else topic_part
                                )
                            }
                        )

            if len(sections) > 1:  # Analysis
                analysis = (
                    "\n".join(sections[1:-1]) if len(sections) > 2 else sections[1]
                )

            if (
                len(sections) > 2
            ):  # Recommendations (if analysis took more than one section)
                recommendation_section_index = 1 + (1 if analysis else 0)
                if len(sections) > recommendation_section_index:
                    rec_lines = sections[recommendation_section_index].split("\n")
                    for line in rec_lines:
                        if line.strip().startswith("- "):
                            recommendations.append(line.strip()[2:])
            elif (
                len(sections) == 2 and not analysis
            ):  # If only two sections and first was trends, second is recs
                rec_lines = sections[1].split("\n")
                for line in rec_lines:
                    if line.strip().startswith("- "):
                        recommendations.append(line.strip()[2:])

            return {
                "trends": trends,
                "analysis": analysis,
                "recommendations": recommendations,
            }
        except Exception as e:
            return {
                "trends": [{"topic": "Error parsing trends"}],
                "analysis": f"Error parsing analysis: {str(e)}. Raw: {result}",
                "recommendations": ["Review raw analysis output"],
            }

    def _parse_generic_result(self, result: str) -> Dict[str, Any]:
        """A generic parser for the run method's output."""
        # This is a placeholder. Actual implementation would depend on expected LLM output format for `run`.
        # For now, returning a simple structure.
        return {
            "raw_output": result,
            "summary": "Analysis complete. Review raw_output for details.",
        }
