from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app import agent as agent_module
from app.tools import tools
from app.tools.requirements_helper import (
    format_confirmation_prompt,
    format_requirement_section,
)
from google.adk.sessions.state import State


def _assert_iso8601_utc(timestamp: str) -> None:
    """Helper that ensures timestamps parse as UTC ISO 8601 strings."""
    assert timestamp.endswith("Z"), f"{timestamp} is missing terminal 'Z'"
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None, "Timestamp must include timezone info"


def test_recommend_books_action_returns_iso_timestamp():
    request = tools.BookRecommendationRequest(
        patron=tools.PatronDetails(name="Casey Doe")
    )

    response = tools.recommend_books_action(request)

    assert len(response.recommendations) == 5
    _assert_iso8601_utc(response.generated_at)


def test_issue_card_action_sets_iso_expiry():
    request = tools.CardRequest(patron=tools.PatronDetails(name="Rio Doe"))

    response = tools.issue_card_action(request)

    _assert_iso8601_utc(response.expires_at)
    expiry = datetime.fromisoformat(response.expires_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    assert expiry > now, "Expiry timestamp should be in the future"


@pytest.mark.parametrize(
    "tool_instance",
    [
        tools.recommend_books,
        tools.order_book,
        tools.issue_library_card,
        tools.add_household_member,
        tools.request_library_event,
        tools.save_conversation_state,
    ],
)
def test_function_tools_generate_declarations(tool_instance):
    declaration = tool_instance._get_declaration()

    assert declaration is not None
    assert declaration.parameters is not None
    assert declaration.parameters.properties, "schema properties must exist"


def test_format_requirement_section_reflects_model_schema():
    text = format_requirement_section(
        tools.BookOrderRequest,
        heading="Collect for BookOrderRequest:",
    )

    assert "Collect for BookOrderRequest:" in text
    assert "patron.name (required)" in text
    assert "needed_by (optional)" in text


def test_requirement_section_lists_nested_collection_fields():
    text = format_requirement_section(tools.CardRequest)

    assert "household_members (optional)" in text
    assert "household_members[].name" in text


def test_confirmation_prompt_requires_explicit_yes():
    text = format_confirmation_prompt(
        tools.BookRecommendationRequest,
        heading="Confirm BookRecommendationRequest:",
    )

    assert "Confirm BookRecommendationRequest:" in text
    assert "Confirm patron.name (required)" in text
    assert "explicit yes/no" in text


def test_agent_instructions_embed_confirmation_blocks_and_state_tool():
    assert (
        "save_conversation_state" in agent_module.book_matching_agent.instruction
    )
    assert (
        agent_module.book_recommendation_confirmation
        in agent_module.book_matching_agent.instruction
    )
    assert (
        agent_module.root_confirmation_sections
        in agent_module.root_agent.instruction
    )


def test_save_conversation_state_action_updates_state():
    ctx = SimpleNamespace(state=State(value={}, delta={}))
    update = tools.ConversationStateUpdate(
        recommendation=tools.BookRecommendationRequest(
            patron=tools.PatronDetails(name="Lakshmi Ray"),
            favorite_genres=["mystery"],
            recent_reads=["In the Woods"],
        ),
        last_confirmation_note="Patron approved recommendations.",
    )

    response = tools.save_conversation_state_action(update, ctx)

    stored = ctx.state[tools.LIBRARY_STATE_KEY]
    assert stored["recommendation"]["patron"]["name"] == "Lakshmi Ray"
    assert "recommendation" in response.applied_fields
    assert stored["last_confirmation_note"] == "Patron approved recommendations."


def test_save_conversation_state_action_merges_sections():
    ctx = SimpleNamespace(state=State(value={}, delta={}))
    first = tools.ConversationStateUpdate(
        card_request=tools.CardRequest(
            patron=tools.PatronDetails(name="Dev"),
            household_members=[],
        )
    )
    tools.save_conversation_state_action(first, ctx)

    second = tools.ConversationStateUpdate(
        event_request=tools.EventRequest(
            patron=tools.PatronDetails(name="Dev"),
            event_type="Book Club",
        )
    )
    tools.save_conversation_state_action(second, ctx)

    stored = ctx.state[tools.LIBRARY_STATE_KEY]
    assert "card_request" in stored
    assert stored["event_request"]["event_type"] == "Book Club"


def test_save_conversation_state_action_accepts_dict_payload():
    ctx = SimpleNamespace(state=State(value={}, delta={}))
    update_dict = {
        "household_request": {
            "primary_card_number": "CARD-42",
            "new_member": {"name": "Gina Boulder"},
        },
        "last_confirmation_note": "Household updated.",
    }

    response = tools.save_conversation_state_action(update_dict, ctx)

    stored = ctx.state[tools.LIBRARY_STATE_KEY]
    assert stored["household_request"]["primary_card_number"] == "CARD-42"
    assert stored["household_request"]["new_member"]["name"] == "Gina Boulder"
    assert stored["last_confirmation_note"] == "Household updated."
    assert set(response.applied_fields) == {
        "household_request",
        "last_confirmation_note",
    }
