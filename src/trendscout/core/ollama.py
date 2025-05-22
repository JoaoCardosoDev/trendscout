import httpx
import json
import asyncio
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import get_settings
from .logging import logger

settings = get_settings()


class ModelNotLoadedError(Exception):
    """Raised when a required model is not loaded in Ollama."""

    pass


class OllamaService:
    """Service for interacting with Ollama API."""

    MAX_RETRIES = 3
    MIN_WAIT = 1  # minimum wait time in seconds
    MAX_WAIT = 10  # maximum wait time in seconds

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=MIN_WAIT, max=MAX_WAIT),
        reraise=True,
    )
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Ollama with retry mechanism."""
        model = model or self.default_model

        # Check if model is loaded
        await self.ensure_model_loaded(model)

        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()["response"]
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error during generation: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=MIN_WAIT, max=MAX_WAIT),
        reraise=True,
    )
    async def list_models(self) -> list[str]:
        """List available models in Ollama with retry mechanism."""
        url = f"{self.base_url}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return [model["name"] for model in response.json()["models"]]
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error while listing models: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=MIN_WAIT, max=MAX_WAIT),
        reraise=True,
    )
    async def pull_model(self, model: str) -> None:
        """Pull a model from Ollama with retry mechanism."""
        url = f"{self.base_url}/api/pull"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json={"name": model})
                response.raise_for_status()
                logger.info(f"Successfully pulled model: {model}")
        except httpx.HTTPError as e:
            logger.error(f"Ollama API error while pulling model {model}: {str(e)}")
            raise

    async def ensure_model_loaded(self, model: str) -> None:
        """Ensure that a model is loaded and ready for use."""
        try:
            models = await self.list_models()
            if model not in models:
                logger.warning(f"Model {model} not found, attempting to pull...")
                await self.pull_model(model)
        except Exception as e:
            logger.error(f"Error checking/loading model {model}: {str(e)}")
            raise ModelNotLoadedError(
                f"Failed to ensure model {model} is loaded: {str(e)}"
            )

    async def check_health(self) -> bool:
        """Check if Ollama service is healthy and responding."""
        try:
            await self.list_models()
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False


# Global Ollama service instance
ollama_service = OllamaService()
