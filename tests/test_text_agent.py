"""
Basic functionality tests for text moderation agent.

Uses pydantic AI's TestModel to avoid real API calls while still validating
that the Agent is configured correctly with proper instructions and schema.
"""

import pytest
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from multimodal_moderation.agents.text_agent import moderate_text, text_moderation_agent
from multimodal_moderation.types.moderation_result import TextModerationResult
from multimodal_moderation.env import get_default_model_choice

models.ALLOW_MODEL_REQUESTS = False


def _get_model():
    return get_default_model_choice()


def test_moderate_text_exists():
    assert callable(moderate_text), "moderate_text should be a callable function"


async def test_moderate_text_returns_text_moderation_result():
    model = _get_model()

    with text_moderation_agent.override(model=TestModel()):
        result = await moderate_text(model, "Hello, how can I help you today?")

    assert isinstance(result, TextModerationResult), \
        f"moderate_text should return TextModerationResult, got {type(result)}"


async def test_moderate_text_has_required_fields():
    model = _get_model()

    with text_moderation_agent.override(model=TestModel()):
        result = await moderate_text(model, "Hello, how can I help you today?")

    assert hasattr(result, 'contains_pii'), "Result must have 'contains_pii' field"
    assert hasattr(result, 'is_unfriendly'), "Result must have 'is_unfriendly' field"
    assert hasattr(result, 'is_unprofessional'), "Result must have 'is_unprofessional' field"
    assert hasattr(result, 'rationale'), "Result must have 'rationale' field"

    assert isinstance(result.contains_pii, bool), "contains_pii should be a boolean"
    assert isinstance(result.is_unfriendly, bool), "is_unfriendly should be a boolean"
    assert isinstance(result.is_unprofessional, bool), "is_unprofessional should be a boolean"
    assert isinstance(result.rationale, str), "rationale should be a string"


async def test_moderate_text_rationale_not_empty():
    model = _get_model()

    with text_moderation_agent.override(model=TestModel()):
        result = await moderate_text(model, "Hello, how can I help you today?")

    assert result.rationale, "Rationale should not be empty"
    assert len(result.rationale) > 0, "Rationale should contain text"
