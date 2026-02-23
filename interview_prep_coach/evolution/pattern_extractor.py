"""AI-powered pattern extraction from conversations."""

import json
from typing import Optional
from pydantic import BaseModel, Field
from anthropic import Anthropic


EXTRACTION_PROMPT = """Analyze this conversation exchange for interview preparation insights.

User message: {user_message}
Assistant response: {assistant_response}

Extract:
1. Weaknesses: Topics or skills the user struggles with (be specific)
2. Strengths: Techniques or areas where the user shows competence
3. Engagement: How engaged is the user? (high/medium/low)

Respond in JSON format only, no other text:
{{"weaknesses": ["..."], "strengths": ["..."], "engagement_level": "high|medium|low"}}

If nothing notable found, return empty arrays and "medium" engagement."""


class ExtractionResult(BaseModel):
    """Results of pattern extraction from a conversation exchange."""

    weaknesses: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    engagement_level: str = "medium"


class PatternExtractor:
    """Extracts patterns from conversation using AI."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def extract(self, user_message: str, assistant_response: str) -> ExtractionResult:
        """Extract insights from a conversation exchange using AI."""
        prompt = EXTRACTION_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response,
        )

        response = self.client.messages.create(
            model="claude-haiku-3-5-20241022",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            data = json.loads(response.content[0].text)
            return ExtractionResult(
                weaknesses=data.get("weaknesses", []),
                strengths=data.get("strengths", []),
                engagement_level=data.get("engagement_level", "medium"),
            )
        except (json.JSONDecodeError, KeyError):
            return ExtractionResult()
