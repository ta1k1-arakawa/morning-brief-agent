from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI, OpenAIError


class OpenAIClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAIClient:
    api_key: str
    model: str
    timeout_seconds: int = 30

    def generate_text(self, prompt: str) -> str:
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise OpenAIClientError("OpenAI prompt must not be empty")

        client = OpenAI(
            api_key=self.api_key,
            timeout=self.timeout_seconds,
        )

        try:
            response = client.responses.create(
                model=self.model,
                input=cleaned_prompt,
            )
        except OpenAIError as exc:
            raise OpenAIClientError(f"Failed to call OpenAI API: {exc}") from exc

        generated_text = response.output_text.strip()

        if not generated_text:
            raise OpenAIClientError("OpenAI API returned an empty response")

        return generated_text
