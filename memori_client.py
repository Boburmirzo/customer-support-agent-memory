"""
Memori API Client

This module provides a client for interacting with the Memori API to store and retrieve
conversational context, enabling personalized customer support experiences.
"""

import os
from typing import Optional, Dict, Any
import httpx


class MemoriClient:
    """Client for interacting with Memori API"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Memori client

        Args:
            api_key: Optional API key (defaults to MEMORI_API_KEY env var)
            base_url: Optional base URL (defaults to production Memori API)
        """
        self.api_key = api_key or os.getenv("MEMORI_API_KEY")
        self.base_url = base_url or "https://memori-api-89r6e.ondigitalocean.app"

    async def chat(
        self,
        content: str,
        user_id: str,
        session_id: str,
        assistant_id: str = "support-bot",
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chat with Memori API to store and retrieve conversational context.

        Args:
            content: The content/message to send to Memori
            user_id: Unique identifier for the user
            session_id: Session identifier for conversation context
            assistant_id: Identifier for the assistant (default: support-bot)
            model: Model to use for the chat (default: gpt-4o-mini)
            temperature: Temperature for response generation (default: 0.7)
            api_key: API key to use for this request (overrides instance api_key)

        Returns:
            Dictionary with:
                - success: bool indicating if the call was successful
                - response: str with the Memori response
                - memory_context: dict with memory metadata
                - conversation_stored: bool indicating if conversation was stored
                - error: str with error message (if success=False)
        """
        # Use provided API key or instance API key
        used_api_key = api_key or self.api_key

        if not used_api_key:
            return {
                "success": False,
                "error": "No API key provided and MEMORI_API_KEY environment variable not set",
            }

        try:
            # Prepare request
            url = f"{self.base_url}/v1/chat"
            headers = {
                "Authorization": f"Bearer {used_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "context": {
                    "assistant_id": assistant_id,
                    "session_id": session_id,
                    "user_id": user_id,
                },
                "messages": [{"content": content, "role": "user"}],
                "model": model,
                "temperature": temperature,
            }

            print(f"DEBUG: Calling Memori API - user: {user_id}, session: {session_id}")

            # Make the API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                memori_response = data.get("response", "")
                memory_context = data.get("memory_context", {})
                memories_used = memory_context.get("memories_used", 0)
                conversation_stored = data.get("conversation_stored", False)

                print(
                    f"DEBUG: Memori API success - memories used: {memories_used}, stored: {conversation_stored}"
                )

                return {
                    "success": True,
                    "response": memori_response,
                    "memory_context": memory_context,
                    "memories_used": memories_used,
                    "conversation_stored": conversation_stored,
                }
            else:
                error_msg = (
                    f"Memori API error: {response.status_code} - {response.text}"
                )
                print(f"ERROR: {error_msg}")
                return {"success": False, "error": error_msg}

        except httpx.TimeoutException as e:
            error_msg = f"Memori API timeout: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error in Memori chat: {str(e)}"
            print(f"ERROR: {error_msg}")
            return {"success": False, "error": error_msg}

    async def get_context(
        self,
        user_id: str,
        session_id: str,
        assistant_id: str = "support-bot",
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve conversational context from Memori without sending a message.

        Args:
            user_id: Unique identifier for the user
            session_id: Session identifier for conversation context
            assistant_id: Identifier for the assistant (default: support-bot)
            api_key: API key to use for this request (overrides instance api_key)

        Returns:
            Dictionary with success status and context data
        """
        # Use an empty message to just retrieve context
        return await self.chat(
            content="",
            user_id=user_id,
            session_id=session_id,
            assistant_id=assistant_id,
            api_key=api_key,
        )


# Backward compatibility function
async def call_memori_chat(
    content: str,
    user_id: str,
    session_id: str,
    api_key: Optional[str] = None,
    assistant_id: str = "support-bot",
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Calls Memori API to store and retrieve conversational context.

    Args:
        content: The message content
        user_id: User identifier
        session_id: Session identifier
        api_key: Optional Memori API key (uses env var if not provided)
        assistant_id: Assistant identifier (default: support-bot)
        model: Model to use (default: gpt-4o-mini)
        temperature: Temperature for generation (default: 0.7)

    Returns:
        Dictionary with Memori response and metadata
    """
    client = MemoriClient(api_key=api_key)
    result = await client.chat(
        content=content,
        user_id=user_id,
        session_id=session_id,
        assistant_id=assistant_id,
        model=model,
        temperature=temperature,
    )

    # Transform response to match old format (with 'context' field)
    if result.get("success"):
        result["context"] = result.get("response", "")

    return result
