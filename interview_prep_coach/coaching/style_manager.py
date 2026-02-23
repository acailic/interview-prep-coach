"""Coaching style management for adaptive feedback."""

import re
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class StyleDimension(str, Enum):
    """Dimensions of coaching style."""
    DIRECTNESS = "directness"
    ENCOURAGEMENT = "encouragement"
    APPROACH = "approach"
    DEPTH = "depth"


class CoachingStyle(BaseModel):
    """Configuration for coaching communication style."""
    directness: str = "medium"
    encouragement: str = "measured"
    approach: str = "collaborative"
    depth: str = "thorough"

    def is_valid_directness(self, value: str) -> bool:
        return value in ("low", "medium", "high")

    def is_valid_encouragement(self, value: str) -> bool:
        return value in ("cheerleader", "measured", "challenging")

    def is_valid_approach(self, value: str) -> bool:
        return value in ("socratic", "instructional", "collaborative")

    def is_valid_depth(self, value: str) -> bool:
        return value in ("concise", "thorough")


class StyleManager(BaseModel):
    """Manages adaptive coaching style based on feedback."""

    current_style: CoachingStyle = Field(default_factory=CoachingStyle)
    effective_styles: list[str] = Field(default_factory=list)

    def adjust(self, dimension: StyleDimension, value: str) -> None:
        if dimension == StyleDimension.DIRECTNESS:
            if self.current_style.is_valid_directness(value):
                self.current_style.directness = value
        elif dimension == StyleDimension.ENCOURAGEMENT:
            if self.current_style.is_valid_encouragement(value):
                self.current_style.encouragement = value
        elif dimension == StyleDimension.APPROACH:
            if self.current_style.is_valid_approach(value):
                self.current_style.approach = value
        elif dimension == StyleDimension.DEPTH:
            if self.current_style.is_valid_depth(value):
                self.current_style.depth = value

    def learn_from_feedback(self, feedback: str, explicit: bool = False) -> None:
        feedback_lower = feedback.lower()

        directness_adjustments = {
            r"(?:be|more)\s+(?:more\s+)?direct": ("directness", "high"),
            r"too\s+(?:harsh|blunt|direct)": ("directness", "low"),
            r"too\s+(?:soft|gentle|vague)": ("directness", "high"),
            r"be\s+(?:more\s+)?gentle": ("directness", "low"),
        }

        encouragement_adjustments = {
            r"(?:be|more)\s+(?:more\s+)?encouraging": ("encouragement", "cheerleader"),
            r"too\s+(?:critical|negative|tough)": ("encouragement", "cheerleader"),
            r"too\s+(?:positive|cheerful|pandering)": ("encouragement", "challenging"),
            r"push\s+(?:me\s+)?(?:harder|more)": ("encouragement", "challenging"),
            r"(?:be|more)\s+(?:more\s+)?challenging": ("encouragement", "challenging"),
        }

        approach_adjustments = {
            r"(?:tell|give)\s+me\s+(?:the\s+)?answer": ("approach", "instructional"),
            r"just\s+(?:tell|give)\s+": ("approach", "instructional"),
            r"(?:ask|guide)\s+me\s+(?:through|to)": ("approach", "socratic"),
            r"(?:use|more)\s+(?:socratic|questions)": ("approach", "socratic"),
            r"(?:work|let'?s\s+work)\s+together": ("approach", "collaborative"),
        }

        depth_adjustments = {
            r"(?:be|give|more)\s+(?:more\s+)?(?:brief|concise|short)": ("depth", "concise"),
            r"too\s+(?:long|wordy|verbose)": ("depth", "concise"),
            r"(?:be|more|go)\s+(?:more\s+)?(?:detailed|in[- ]?depth|thorough)": ("depth", "thorough"),
            r"(?:need|want|give)\s+(?:me\s+)?(?:more\s+)?detail": ("depth", "thorough"),
        }

        all_adjustments = {
            **directness_adjustments,
            **encouragement_adjustments,
            **approach_adjustments,
            **depth_adjustments,
        }

        for pattern, (dimension_name, value) in all_adjustments.items():
            if re.search(pattern, feedback_lower):
                dimension = StyleDimension(dimension_name)
                self.adjust(dimension, value)
                if explicit:
                    style_key = f"{dimension_name}:{value}"
                    if style_key not in self.effective_styles:
                        self.effective_styles.append(style_key)
                break

    def record_outcome(self, style_used: str, improved: bool) -> None:
        if improved:
            if style_used not in self.effective_styles:
                self.effective_styles.append(style_used)
        elif style_used in self.effective_styles:
            self.effective_styles.remove(style_used)

    def get_system_prompt_modifier(self) -> str:
        parts = []

        directness_guidance = {
            "low": "Be gentle and supportive in feedback. Use soft language.",
            "medium": "Be clear and balanced in feedback.",
            "high": "Be direct and straightforward. Don't sugarcoat.",
        }
        parts.append(directness_guidance[self.current_style.directness])

        encouragement_guidance = {
            "cheerleader": "Offer enthusiastic praise and encouragement. Celebrate wins.",
            "measured": "Provide balanced feedback with appropriate acknowledgment.",
            "challenging": "Focus on areas for growth. Push for improvement.",
        }
        parts.append(encouragement_guidance[self.current_style.encouragement])

        approach_guidance = {
            "socratic": "Guide through questions. Help them discover answers.",
            "instructional": "Provide clear explanations and direct guidance.",
            "collaborative": "Work together. Balance guidance with exploration.",
        }
        parts.append(approach_guidance[self.current_style.approach])

        depth_guidance = {
            "concise": "Keep responses brief and to the point.",
            "thorough": "Provide detailed, comprehensive responses.",
        }
        parts.append(depth_guidance[self.current_style.depth])

        return " ".join(parts)
