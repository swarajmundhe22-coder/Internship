from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings


class CopilotService:
    MODEL_QUERY = "openai/gpt-oss-120b"
    MODEL_DOC = "openai/gpt-oss-120b"
    MODEL_SEARCH = "openai/gpt-oss-120b"

    def __init__(self) -> None:
        get_settings.cache_clear()
        self.settings = get_settings()
        self.client: OpenAI | None = None
        if self.settings.nvidia_api_key:
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=self.settings.nvidia_api_key,
            )

    def query(self, user_input: str) -> tuple[str, str]:
        return self._run_completion(model=self.MODEL_QUERY, user_input=user_input)

    def doc(self, user_input: str) -> tuple[str, str]:
        return self._run_completion(model=self.MODEL_DOC, user_input=user_input)

    def search(self, user_input: str) -> tuple[str, str]:
        return self._run_completion(model=self.MODEL_SEARCH, user_input=user_input)

    def _run_completion(self, *, model: str, user_input: str) -> tuple[str, str]:
        if self.client is None:
            fallback = (
                "NVIDIA copilot key is not configured. Configure NVIDIA_API_KEY to enable "
                "live model inference."
            )
            return fallback, model

        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_input}],
                temperature=1,
                top_p=1,
                max_tokens=4096,
            )
        except Exception as exc:
            fallback = (
                "NVIDIA copilot request failed. Verify NVIDIA_API_KEY validity, model access, and account permissions. "
                f"Provider detail: {type(exc).__name__}."
            )
            return fallback, model

        choice = completion.choices[0]
        content = getattr(choice.message, "content", None)
        if not content:
            content = "Model response was empty."
        return str(content), model
