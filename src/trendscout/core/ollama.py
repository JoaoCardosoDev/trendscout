import httpx
import json
from typing import Any, Dict, Optional
from .config import get_settings

settings = get_settings()

class OllamaService:
    """Service for interacting with Ollama API."""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate text using Ollama."""
        model = model or self.default_model
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
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        url = f"{self.base_url}/api/tags"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return [model["name"] for model in response.json()["models"]]
        except httpx.HTTPError as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    async def pull_model(self, model: str) -> None:
        """Pull a model from Ollama."""
        url = f"{self.base_url}/api/pull"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json={"name": model})
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise Exception(f"Ollama API error: {str(e)}")

# Global Ollama service instance
ollama_service = OllamaService()
