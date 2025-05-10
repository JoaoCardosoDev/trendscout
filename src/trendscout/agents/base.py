from abc import ABC, abstractmethod
from crewai import Agent
from typing import Any, Dict, Optional
from ..core.ollama import ollama_service
from ..core.config import get_settings

settings = get_settings()

class BaseAgent(ABC):
    """Base class for all Trendscout agents."""
    
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.model = model or settings.OLLAMA_MODEL
        self.temperature = temperature
        self.kwargs = kwargs
        self._agent: Agent | None = None

    @property
    def agent(self) -> Agent:
        """Get or create the CrewAI agent instance."""
        if self._agent is None:
            self._agent = Agent(
                name=self.name,
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                llm=self._create_ollama_callback(),
                **self.kwargs
            )
        return self._agent

    def _create_ollama_callback(self):
        """Create a callback function for CrewAI to use Ollama."""
        async def ollama_call(prompt: str, system_prompt: Optional[str] = None) -> str:
            return await ollama_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=self.model,
                temperature=self.temperature
            )
        return ollama_call

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Dict[str, Any]) -> Any:
        """Execute the agent's primary task."""
        pass

    @abstractmethod
    async def validate_result(self, result: Any) -> bool:
        """Validate the result of the agent's execution."""
        pass
