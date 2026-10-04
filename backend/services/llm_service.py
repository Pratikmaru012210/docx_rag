from typing import List, Dict, Any, Generator, Optional
from groq import Groq

from backend.config import settings
from backend.constants import SYSTEM_INSTRUCTION_SOP, ERROR_GROQ_KEY_MISSING


class LLMService:
    """Manages Groq LLM completions, prompt construction, and streaming generation."""

    def __init__(self):
        """Initialize the lazy client cache for Groq requests."""
        self._groq: Optional[Groq] = None

    def get_client(self) -> Groq:
        """Lazily initialize the Groq client after confirming the API key is configured."""
        if not self._groq:
            if not settings.GROQ_API_KEY:
                raise ValueError(ERROR_GROQ_KEY_MISSING)
            self._groq = Groq(api_key=settings.GROQ_API_KEY)
        return self._groq

    def build_prompt_messages(
        self, query: str, context_chunks: List[Dict[str, Any]], chat_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """Constructs augmented prompt with system instructions, retrieved context blocks, and history."""
        context_blocks = []
        for i, c in enumerate(context_chunks, 1):
            context_blocks.append(
                f"### [Source #{i}] - {c['breadcrumb']} ({c['content_type'].upper()})\n"
                f"{c['text']}"
            )
        combined_context = "\n\n---\n\n".join(context_blocks)

        user_content = (
            f"Retrieved Document Context:\n"
            f"```\n{combined_context}\n```\n\n"
            f"User Question:\n{query}"
        )

        messages = [{"role": "system", "content": SYSTEM_INSTRUCTION_SOP}]

        if chat_history:
            # Bound prompt growth by sending only the latest four conversation messages.
            for msg in chat_history[-4:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_content})
        return messages

    def stream_completion(
        self, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 2048
    ) -> Generator[str, None, None]:
        """Streams generated tokens from Groq API."""
        groq = self.get_client()
        stream = groq.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token
