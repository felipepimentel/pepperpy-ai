"""StackSpot AI LLM provider implementation using Knowledge Sources."""

import aiohttp
import json
import logging
import uuid
from typing import Dict, Any, Optional, List

from pepperpy.llm import LLMProvider
from pepperpy.plugin import ProviderPlugin
from pepperpy.core.errors import LLMError, AuthenticationError

class StackSpotAIProvider(LLMProvider, ProviderPlugin):
    """StackSpot AI LLM provider implementation using Knowledge Sources.
    
    This provider uses the StackSpot AI Knowledge Sources API to store and query
    information, since direct access to chat/completions APIs may be restricted.
    """
    
    # Configuration attributes
    client_id: str
    client_secret: str
    realm: str = "stackspot-freemium"
    api_url: str = "https://genai-code-buddy-api.stackspot.com/v1"
    auth_url: str = "https://idm.stackspot.com"
    ks_name: str = "pepperpy-ks"
    
    # Internal state
    _token: Optional[str] = None
    _session: Optional[aiohttp.ClientSession] = None
    _initialized: bool = False
    _knowledge_source_slug: Optional[str] = None
    
    def __init__(self, **kwargs):
        """Initialize with configuration.
        
        Args:
            **kwargs: Configuration parameters including client_id, client_secret, etc.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Set attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @property
    def initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized
    
    async def initialize(self) -> None:
        """Initialize the StackSpot AI provider."""
        if self._initialized:
            return
            
        self.logger.debug("Initializing StackSpot AI provider")
        
        self._session = aiohttp.ClientSession()
        
        # Authenticate to get token
        await self._authenticate()
        
        # Set up knowledge source
        await self._setup_knowledge_source()
        
        self._initialized = True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None
            self._token = None
        self._initialized = False
    
    async def _authenticate(self) -> None:
        """Authenticate with StackSpot AI and get an access token."""
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        auth_endpoint = f"{self.auth_url}/{self.realm}/oidc/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        self.logger.info(f"Authenticating with StackSpot AI at {auth_endpoint}")
        
        try:
            async with self._session.post(auth_endpoint, data=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Authentication failed with status {response.status}: {error_text}")
                    raise AuthenticationError(f"Failed to authenticate with StackSpot AI: {error_text}")
                
                result = await response.json()
                self._token = result.get('access_token')
                
                if not self._token:
                    self.logger.error("No access token found in authentication response")
                    raise AuthenticationError("No access token found in authentication response")
                    
                self.logger.info("Successfully authenticated with StackSpot AI")
                self.logger.debug(f"Token: {self._token[:10]}...")
        except Exception as e:
            self.logger.error(f"Error during authentication: {str(e)}")
            raise AuthenticationError(f"Error during StackSpot AI authentication: {str(e)}")
    
    async def _ensure_authenticated(self) -> None:
        """Ensure that we have a valid authentication token."""
        if not self._token:
            await self._authenticate()
    
    async def _setup_knowledge_source(self) -> None:
        """Set up a knowledge source for storing and retrieving information."""
        await self._ensure_authenticated()
        
        # First check if we already have a knowledge source
        headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json'
        }
        
        self.logger.info("Checking for existing knowledge sources")
        async with self._session.get(f"{self.api_url}/knowledge-sources", headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                self.logger.error(f"Failed to list knowledge sources: {error_text}")
                raise LLMError(f"Failed to list knowledge sources: {error_text}")
            
            sources = await response.json()
            
            if sources and len(sources) > 0:
                # Use the first existing knowledge source
                self._knowledge_source_slug = sources[0].get('slug')
                self.logger.info(f"Using existing knowledge source: {self._knowledge_source_slug}")
                return
            
            # No existing knowledge source, create a new one
            self.logger.info("No existing knowledge source found, creating a new one")
            
            # Generate a unique slug
            unique_id = str(uuid.uuid4())[:8]
            slug = f"pepperpy-ks-{unique_id}"
            
            payload = {
                "slug": slug,
                "name": f"PepperPy Knowledge Source {unique_id}",
                "description": "Knowledge source for PepperPy LLM provider",
                "type": "CUSTOM"
            }
            
            async with self._session.post(f"{self.api_url}/knowledge-sources", json=payload, headers=headers) as response:
                if response.status != 201 and response.status != 204 and response.status != 200:
                    error_text = await response.text()
                    self.logger.error(f"Failed to create knowledge source: {error_text}")
                    raise LLMError(f"Failed to create knowledge source: {error_text}")
                
                self._knowledge_source_slug = slug
                self.logger.info(f"Created new knowledge source: {slug}")
    
    async def _add_content(self, content: str) -> None:
        """Add content to the knowledge source."""
        if not self._knowledge_source_slug:
            await self._setup_knowledge_source()
            
        await self._ensure_authenticated()
        
        headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "content": content
        }
        
        self.logger.info(f"Adding content to knowledge source {self._knowledge_source_slug}")
        async with self._session.post(f"{self.api_url}/knowledge-sources/{self._knowledge_source_slug}/custom", json=payload, headers=headers) as response:
            if response.status > 299:
                error_text = await response.text()
                self.logger.error(f"Failed to add content: {error_text}")
                raise LLMError(f"Failed to add content: {error_text}")
            
            self.logger.info("Content added successfully")
    
    async def _query_knowledge_source(self, query: str) -> str:
        """Query the knowledge source. Se não for permitido, retorna mensagem de fallback."""
        if not self._knowledge_source_slug:
            await self._setup_knowledge_source()
        await self._ensure_authenticated()
        headers = {
            'Authorization': f'Bearer {self._token}',
            'Content-Type': 'application/json'
        }
        payload = {"query": query}
        self.logger.info(f"Querying knowledge source {self._knowledge_source_slug} with: {query}")
        async with self._session.post(f"{self.api_url}/knowledge-sources/{self._knowledge_source_slug}/query", json=payload, headers=headers) as response:
            if response.status == 403:
                self.logger.warning("Query not permitted for this account. Fallback to upload-only mode.")
                return "[INFO] Querying knowledge sources is not available for your account. Content was uploaded, but cannot be queried (freemium limitation)."
            if response.status != 200:
                error_text = await response.text()
                self.logger.error(f"Failed to query knowledge source: {error_text}")
                return f"Unable to query knowledge source: {error_text}. Your credentials may not have the required permissions."
            result = await response.json()
            answer = result.get("answer", "No answer provided by the knowledge source")
            self.logger.info(f"Query result: {answer}")
            return answer
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Complete a prompt using StackSpot AI.
        
        Since direct chat/completions API may not be available, this
        implementation uses Knowledge Sources as an alternative.
        
        Args:
            prompt: The prompt to complete
            **kwargs: Additional parameters
            
        Returns:
            Completion text
            
        Raises:
            LLMError: If the API call fails
        """
        try:
            # First add the prompt as content to the knowledge source
            await self._add_content(f"Question: {prompt}")
            
            # Then query the knowledge source with the same prompt
            result = await self._query_knowledge_source(prompt)
            return result
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error: {str(e)}")
            raise LLMError(f"HTTP error during StackSpot AI API call: {str(e)}")
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            self.logger.error(f"Error during completion: {str(e)}")
            raise LLMError(f"Error during StackSpot AI completion: {str(e)}")
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Chat with StackSpot AI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
            
        Raises:
            LLMError: If the API call fails
        """
        try:
            # Convert messages to a single prompt
            content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # Add to knowledge source
            await self._add_content(content)
            
            # Query with the last user message
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            query = user_messages[-1]['content'] if user_messages else "Hello"
            
            answer = await self._query_knowledge_source(query)
            
            # Format as a chat response
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": answer
                        },
                        "finish_reason": "stop",
                        "index": 0
                    }
                ]
            }
                
        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP error: {str(e)}")
            raise LLMError(f"HTTP error during StackSpot AI API call: {str(e)}")
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            self.logger.error(f"Error during chat: {str(e)}")
            raise LLMError(f"Error during StackSpot AI chat: {str(e)}")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM functionality.
        
        Args:
            input_data: Input data containing task and parameters
            
        Returns:
            Response dictionary with status and result
        """
        try:
            task = input_data.get("task")
            
            if task == "complete":
                prompt = input_data.get("prompt")
                if not prompt:
                    return {
                        "status": "error",
                        "message": "No prompt provided for completion task"
                    }
                
                # Create a copy of input_data and remove the prompt key to avoid duplication
                kwargs = input_data.copy()
                kwargs.pop("task", None)
                kwargs.pop("prompt", None)
                
                completion = await self.complete(prompt, **kwargs)
                return {
                    "status": "success",
                    "result": completion
                }
            
            elif task == "chat":
                messages = input_data.get("messages")
                if not messages:
                    return {
                        "status": "error",
                        "message": "No messages provided for chat task"
                    }
                
                # Create a copy of input_data and remove the messages key to avoid duplication
                kwargs = input_data.copy()
                kwargs.pop("task", None)
                kwargs.pop("messages", None)
                
                chat_result = await self.chat(messages, **kwargs)
                return {
                    "status": "success",
                    "result": chat_result
                }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown task: {task}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def from_config(config: dict) -> "StackSpotAIProvider":
        """Create provider from config dict."""
        required = ["client_id", "client_secret", "realm", "api_url", "auth_url"]
        for key in required:
            if key not in config:
                raise LLMError(f"Missing required config key: {key}")
        return StackSpotAIProvider(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            realm=config["realm"],
            api_url=config["api_url"],
            auth_url=config["auth_url"],
            ks_name=config.get("ks_name", "pepperpy-ks")
        ) 