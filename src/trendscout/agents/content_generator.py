from typing import Any, Dict, List
from crewai import Task # Import Task
from .base import BaseAgent

class ContentGeneratorAgent(BaseAgent):
    """Agent responsible for generating content ideas based on trending topics."""
    
    def __init__(self):
        super().__init__(
            name="Content Generator",
            role="Creative Content Strategist",
            goal="Generate engaging content ideas based on trending topics",
            backstory="Creative expert specializing in transforming trending topics "
                     "into engaging content ideas, with deep understanding of "
                     "audience engagement and viral content mechanics.",
            temperature=0.8  # Slightly higher for more creative outputs
        )

    def run(self, query: str) -> Dict[str, Any]:
        """
        Synchronous method to generate content ideas based on a simple query string (topic/trends).
        This adapts the simple query to the agent's expected input for its underlying CrewAI agent.
        """
        
        prompt = f"""
        As a Creative Content Strategist, generate engaging content ideas based on the following topic or trends:
        
        Topic/Trends: "{query}"
        
        Consider various content types (e.g., blog posts, social media updates, video scripts) and target platforms.
        
        Provide:
        1. A list of creative content ideas.
        2. A brief content strategy overview.
        3. Relevant hashtags.
        4. Tips for maximizing engagement.
        
        Format the response as a structured output.
        """
        
        # Execute content generation using the underlying CrewAI agent
        task = Task(
            description=prompt.strip(),
            agent=self.agent,
            expected_output="A structured list of content ideas, a strategy overview, relevant hashtags, and engagement tips."
        )
        raw_result = self.agent.execute_task(task)
        
        # Parse and structure the result
        structured_result = self._parse_result(raw_result) # _parse_result might need adjustment
        
        return structured_result
        
    async def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Asynchronous method to generate content ideas based on structured trend analysis.
        
        Args:
            data: Dictionary containing trend analysis to base content on
                 Expected format:
                 {
                     "trends": List[Dict],  # Trends from TrendAnalyzer
                     "target_platform": str,  # Platform to create content for
                     "content_types": List[str],  # Required content types
                     "brand_voice": str,  # Brand voice guidelines
                 }
        
        Returns:
            Dict containing generated content ideas:
            {
                "content_ideas": List[Dict],  # List of content ideas
                "strategy": str,  # Content strategy overview
                "hashtags": List[str],  # Relevant hashtags
                "engagement_tips": List[str]  # Tips for maximizing engagement
            }
        """
        # Validate input data
        if not self._validate_input(data):
            raise ValueError("Invalid input data format")
            
        # Create prompt for content generation
        prompt = self._create_generation_prompt(data)
        
        # Generate content ideas using CrewAI agent
        result = await self.agent.execute_task(prompt)
        
        # Parse and structure the result
        structured_result = self._parse_result(result)
        
        return structured_result
        
    async def validate_result(self, result: Dict[str, Any]) -> bool:
        """
        Validate the generated content ideas.
        
        Args:
            result: The content generation result to validate
            
        Returns:
            bool: True if result is valid, False otherwise
        """
        required_keys = {"content_ideas", "strategy", "hashtags", "engagement_tips"}
        
        # Check for required keys
        if not all(key in result for key in required_keys):
            return False
            
        # Validate content ideas structure
        if not isinstance(result["content_ideas"], list) or not result["content_ideas"]:
            return False
            
        # Validate strategy content
        if not isinstance(result["strategy"], str) or not result["strategy"].strip():
            return False
            
        # Validate hashtags
        if not isinstance(result["hashtags"], list) or not result["hashtags"]:
            return False
            
        # Validate engagement tips
        if not isinstance(result["engagement_tips"], list) or not result["engagement_tips"]:
            return False
            
        return True
        
    def _validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data format."""
        required_keys = {"trends", "target_platform", "content_types", "brand_voice"}
        
        if not all(key in data for key in required_keys):
            return False
            
        if not isinstance(data["trends"], list) or not data["trends"]:
            return False
            
        if not isinstance(data["content_types"], list) or not data["content_types"]:
            return False
            
        # Validate platform is supported
        if data["target_platform"].lower() not in {"twitter", "reddit", "instagram", "linkedin"}:
            return False
            
        return True
        
    def _create_generation_prompt(self, data: Dict[str, Any]) -> str:
        """Create a detailed prompt for content generation."""
        trends = "\n".join([f"- {t['topic']}" for t in data["trends"]])
        content_types = ", ".join(data["content_types"])
        
        prompt = f"""
        As a Creative Content Strategist, generate engaging content ideas based on these trends:
        
        Trends:
        {trends}
        
        Target Platform: {data["target_platform"]}
        Content Types Needed: {content_types}
        Brand Voice: {data["brand_voice"]}
        
        Provide:
        1. A list of creative content ideas that align with the trends
        2. A content strategy that ties the ideas together
        3. Relevant hashtags to increase visibility
        4. Tips for maximizing engagement
        
        For each content idea, consider:
        - Platform-specific best practices
        - Brand voice alignment
        - Engagement potential
        - Trend relevance
        - Viral mechanics
        
        Format the response as a structured output that can be parsed into content ideas, strategy, hashtags, and engagement tips.
        """
        
        return prompt.strip()
        
    def _parse_result(self, result: str) -> Dict[str, Any]:
        """Parse and structure the AI model's response."""
        try:
            # Split the content into sections
            sections = result.split("\n\n")
            
            # Extract content ideas (assuming first section)
            content_ideas = [
                {
                    "title": line.strip().split(": ")[1].split(" - ")[0],
                    "description": line.strip().split(" - ")[1]
                }
                for line in sections[0].split("\n")
                if line.strip().startswith("- ")
            ]
            
            # Extract strategy (assuming second section)
            strategy = sections[1] if len(sections) > 1 else ""
            
            # Extract hashtags (assuming third section)
            hashtags = [
                tag.strip()
                for tag in (sections[2].split("\n") if len(sections) > 2 else [])
                if tag.strip().startswith("#")
            ]
            
            # Extract engagement tips (assuming fourth section)
            engagement_tips = [
                line.strip().split("- ")[1]
                for line in (sections[3].split("\n") if len(sections) > 3 else [])
                if line.strip().startswith("- ")
            ]
            
            return {
                "content_ideas": content_ideas,
                "strategy": strategy,
                "hashtags": hashtags,
                "engagement_tips": engagement_tips
            }
            
        except Exception as e:
            # Fallback structure if parsing fails
            return {
                "content_ideas": [{"title": "Error", "description": "Error parsing content ideas"}],
                "strategy": f"Error parsing strategy: {str(e)}",
                "hashtags": ["#error"],
                "engagement_tips": ["Review raw generation output"]
            }
