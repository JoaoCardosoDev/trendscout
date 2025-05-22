from abc import ABC, abstractmethod
from crewai import Agent
from typing import Any, Dict, Optional
from langchain_community.chat_models import ChatLiteLLM
import litellm  # Import litellm
from ..core.config import get_settings

settings = get_settings()

# Try enabling LiteLLM's most verbose internal debugging
try:
    litellm._turn_on_debug()
    print("LiteLLM internal debug mode turned ON.")
except Exception as e:
    print(f"Could not turn on LiteLLM internal debug: {e}")


# We are now relying on OLLAMA_API_BASE_URL environment variable primarily.
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
        **kwargs,
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
            # Initialize ChatLiteLLM for Ollama
            # Relying on OLLAMA_API_BASE_URL environment variable picked up by LiteLLM
            ollama_llm = ChatLiteLLM(
                model=f"ollama/{self.model}",
                temperature=self.temperature,
                request_timeout=settings.OLLAMA_REQUEST_TIMEOUT,
            )

            self._agent = Agent(
                name=self.name,
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                llm=ollama_llm,
                allow_delegation=False,
                verbose=True,
                **self.kwargs,
            )
        return self._agent

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Dict[str, Any]) -> Any:
        """Execute the agent's primary task."""
        pass

    @abstractmethod
    async def validate_result(self, result: Any) -> bool:
        """Validate the result of the agent's execution."""
        pass
