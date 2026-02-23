"""AI-powered pattern extraction from conversations."""

from typing import Optional
from pydantic import BaseModel, Field


EXTRACTION_PROMPT = """Analyze this conversation exchange for interview preparation insights.

User message: {user_message}
Assistant response: {assistant_response}

Extract:
1. Weaknesses: Topics or skills the user struggles with (be specific)
2. Strengths: Techniques or areas where the user shows competence
3. Engagement: How engaged is the user? (high/medium/low)

Respond in JSON format:
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
        self.api_key = api_key

    def extract(self, user_message: str, assistant_response: str) -> ExtractionResult:
        """Extract insights from a conversation exchange."""
        return ExtractionResult()
