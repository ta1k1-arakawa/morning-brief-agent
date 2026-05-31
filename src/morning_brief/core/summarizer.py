from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from morning_brief.core.collector import CollectedBriefData
from morning_brief.core.prompt_builder import PromptBuilder


class OpenAIClient(Protocol):
    def generate_text(self, prompt: str) -> str:
        """Return generated text for the given prompt."""


@dataclass(frozen=True)
class SummaryResult:
    prompt: str
    summary: str


@dataclass(frozen=True)
class BriefSummarizer:
    openai_client: OpenAIClient
    prompt_builder: PromptBuilder = field(default_factory=PromptBuilder)

    def summarize(self, data: CollectedBriefData) -> SummaryResult:
        prompt = self.prompt_builder.build(data)
        summary = self.openai_client.generate_text(prompt)

        return SummaryResult(
            prompt=prompt,
            summary=self._clean_summary(summary),
        )

    def _clean_summary(self, summary: str) -> str:
        cleaned = summary.strip()

        if not cleaned:
            return "今日のブリーフを生成できませんでした。"

        return cleaned


def generate_brief_summary(
    data: CollectedBriefData,
    openai_client: OpenAIClient,
) -> str:
    return BriefSummarizer(openai_client=openai_client).summarize(data).summary
