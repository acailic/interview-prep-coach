"""Extract job context from postings using AI."""

import json
from typing import Optional
from anthropic import Anthropic

from .context import JobContext
from interview_prep_coach.utils.logger import get_logger

logger = get_logger(__name__)

EXTRACTION_PROMPT = """Extract job posting information from this text.

Job Posting:
{posting}

Return JSON with these fields:
- company: Company name
- position: Job title
- requirements: List of key requirements
- tech_stack: List of technologies mentioned
- key_skills: List of important skills

Return only valid JSON, no other text."""


class JobExtractor:
    """Extract job context from postings using Claude Haiku."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def extract(self, posting_text: str) -> JobContext:
        """Extract job context from posting text."""
        prompt = EXTRACTION_PROMPT.format(posting=posting_text)

        try:
            response = self.client.messages.create(
                model="claude-haiku-3-5-20241022",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )

            data = json.loads(response.content[0].text)
            return JobContext(
                company=data.get("company", "Unknown Company"),
                position=data.get("position", "Unknown Position"),
                requirements=data.get("requirements", []),
                tech_stack=data.get("tech_stack", []),
                key_skills=data.get("key_skills", []),
                raw_posting=posting_text,
            )
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse job extraction response: {e}")
            return JobContext(
                company="Unknown Company",
                position="Unknown Position",
                raw_posting=posting_text,
            )
        except Exception as e:
            logger.error(f"Job extraction failed: {e}")
            return JobContext(
                company="Unknown Company",
                position="Unknown Position",
                raw_posting=posting_text,
            )

    def extract_from_file(self, file_path: str) -> JobContext:
        """Extract job context from a file."""
        with open(file_path, "r") as f:
            return self.extract(f.read())

    def extract_from_url(self, url: str) -> JobContext:
        """Extract job context from a URL (fetches content)."""
        import httpx
        from bs4 import BeautifulSoup

        response = httpx.get(url, follow_redirects=True)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text(separator="\n", strip=True)
        return self.extract(text)
