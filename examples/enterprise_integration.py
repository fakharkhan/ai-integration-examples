"""
SOFT PYRAMID LLC
Enterprise AI Integration Example
Contact: +1-385-216-2631
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
import aiohttp
import asyncio

from utils.enterprise_utils import EnterpriseAIUtils, SecurityManager, MonitoringSystem

class EnterpriseAIIntegration:
    """Enterprise AI Integration Example"""

    def __init__(self):
        load_dotenv()
        self.utils = EnterpriseAIUtils()
        self.security = SecurityManager()
        self.monitoring = MonitoringSystem()
        
        # Initialize AI clients
        self.openai_client = OpenAI(
            api_key=self.utils.secure_api_key(os.getenv("OPENAI_API_KEY", ""))
        )
        self.claude_client = Anthropic(
            api_key=self.utils.secure_api_key(os.getenv("ANTHROPIC_API_KEY", ""))
        )
        self.deepseek_api_key = self.utils.secure_api_key(
            os.getenv("DEEPSEEK_API_KEY", "")
        )

    @EnterpriseAIUtils.handle_rate_limits(retry_count=3)
    async def get_completion(self, 
                           provider: str, 
                           prompt: str, 
                           **kwargs) -> Dict[str, Any]:
        """Get completion from specified AI provider"""
        
        if not self.utils.validate_input(prompt):
            raise ValueError("Invalid input detected")

        # Check cache first
        cache_key = f"{provider}:{prompt}"
        cached_response = self.utils.get_cached_response(cache_key)
        if cached_response:
            return cached_response

        try:
            response = await self._route_request(provider, prompt, **kwargs)
            
            # Monitor usage
            self.utils.monitor_usage(
                model=response.get("model", "unknown"),
                tokens=response.get("usage", {}).get("total_tokens", 0),
                cost=self._calculate_cost(response)
            )

            # Cache response
            self.utils.cache_response(cache_key, response)
            
            # Track request
            self.monitoring.track_request({
                "provider": provider,
                "prompt_length": len(prompt),
                "response_length": len(str(response)),
                "status": "success"
            })

            return response

        except Exception as e:
            self.utils.logger.error(f"Completion error: {str(e)}")
            raise

    async def _route_request(self, 
                           provider: str, 
                           prompt: str, 
                           **kwargs) -> Dict[str, Any]:
        """Route request to appropriate provider"""
        
        if provider == "openai":
            return await self._openai_request(prompt, **kwargs)
        elif provider == "claude":
            return await self._claude_request(prompt, **kwargs)
        elif provider == "deepseek":
            return await self._deepseek_request(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _openai_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Handle OpenAI request"""
        response = await self.openai_client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response

    async def _claude_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Handle Claude request"""
        response = await self.claude_client.messages.create(
            model=kwargs.get("model", "claude-3-opus-20240229"),
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response

    async def _deepseek_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Handle DeepSeek request"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": kwargs.get("model", "deepseek-chat"),
                    "messages": [{"role": "user", "content": prompt}],
                    **kwargs
                }
            ) as response:
                return await response.json()

    def _calculate_cost(self, response: Dict[str, Any]) -> float:
        """Calculate cost based on token usage"""
        # Implementation details available through consultation
        return 0.0

async def main():
    """Example usage"""
    integration = EnterpriseAIIntegration()
    
    prompt = "Explain the benefits of enterprise AI integration."
    
    # Example with OpenAI
    openai_response = await integration.get_completion(
        provider="openai",
        prompt=prompt,
        temperature=0.7
    )
    print("OpenAI Response:", openai_response)
    
    # Example with Claude
    claude_response = await integration.get_completion(
        provider="claude",
        prompt=prompt,
        temperature=0.7
    )
    print("Claude Response:", claude_response)
    
    # Example with DeepSeek
    deepseek_response = await integration.get_completion(
        provider="deepseek",
        prompt=prompt,
        temperature=0.7
    )
    print("DeepSeek Response:", deepseek_response)

if __name__ == "__main__":
    asyncio.run(main()) 