from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app import agent as agent_module
from app.tools import tools
from app.tools.requirements_helper import format_requirement_section
from app.tools.question_bank import (
    format_confirmation_checklist,
    format_question_collection,
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


def test_recommend_books_action_accepts_dict_payload():
    request_dict = {
        "patron": {"name": "Priya Banner"},
        "favorite_genres": ["mystery"],
        "recent_reads": ["The Guest List"],
    }

    response = tools.recommend_books_action(request_dict)

    assert response.recommendations
    assert response.recommendations[0].startswith("Mystery")
    _assert_iso8601_utc(response.generated_at)


def test_order_book_action_accepts_dict_payload():
    request_dict = {
        "patron": {"name": "Eve Rider"},
        "title": "Fourth Wing",
        "format": "paperback",
        "shipping_address": {
            "street_line1": "1 Library Way",
            "city": "Stack City",
            "state_or_province": "CA",
            "postal_code": "94016",
            "country": "USA",
        },
        "preferred_vendor": "Local Books",
        "preferred_vendor_address": {
            "street_line1": "2 Vendor Rd",
            "city": "Stack City",
            "state_or_province": "CA",
            "postal_code": "94016",
            "country": "USA",
        },
    }

    response = tools.order_book_action(request_dict)

    assert response.request_id.startswith("ORD-")
    assert response.status == "requested"


def test_issue_card_action_sets_iso_expiry():
    request = tools.CardRequest(patron=tools.PatronDetails(name="Rio Doe"))

    response = tools.issue_card_action(request)

    _assert_iso8601_utc(response.expires_at)
    expiry = datetime.fromisoformat(response.expires_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    assert expiry > now, "Expiry timestamp should be in the future"


def test_issue_card_action_accepts_dict_payload():
    request_dict = {"patron": {"name": "Quinn"}, "household_members": []}

    response = tools.issue_card_action(request_dict)

    assert response.card_number.startswith("CARD-")
    _assert_iso8601_utc(response.expires_at)


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


def test_question_bank_renders_collection_with_prompts_and_validations():
    text = format_question_collection(
        "recommend_books",
        heading="Collect details to populate BookRecommendationRequest:",
        bullet_indent="  ",
    )

    assert "Collect details to populate BookRecommendationRequest:" in text
    assert 'ask: "What\'s the patron\'s full name?"' in text
    assert "validation: non-empty string" in text
    assert "favorite_genres (optional)" in text


def test_question_bank_renders_confirmation_with_notes_and_conditions():
    text = format_confirmation_checklist(
        "recommend_books",
        heading="Before using `recommend_books`, confirm:",
        bullet_indent="    ",
        closing_line="Require an explicit yes before routing.",
    )

    assert "Before using `recommend_books`, confirm:" in text
    assert "Confirm patron.name (required)" in text
    assert "Spell back the name" in text
    assert "Require an explicit yes before routing." in text


def test_question_bank_renders_order_book_details():
    text = format_question_collection(
        "order_book",
        heading="Collect details to populate BookOrderRequest:",
        bullet_indent="  ",
    )

    assert "Collect details to populate BookOrderRequest:" in text
    assert "title (required)" in text
    assert "shipping_address.city (required)" in text
    assert 'ask: "Which vendor should we source the title from?"' in text
    assert "validation: ISO 8601 date" in text


def test_question_bank_confirmation_for_card_services():
    text = format_confirmation_checklist(
        "issue_library_card",
        heading="Before using `issue_library_card`, confirm:",
        bullet_indent="    ",
        closing_line="Remind them about pickup verification and PIN expiry.",
    )

    assert "Before using `issue_library_card`, confirm:" in text
    assert "Confirm patron.name (required)" in text
    assert "Confirm household_members" in text
    assert "Remind them about pickup verification and PIN expiry." in text


def test_question_bank_collection_for_household_linking():
    text = format_question_collection(
        "add_household_member",
        heading="Collect details to populate HouseholdAddRequest:",
        bullet_indent="  ",
    )

    assert "Collect details to populate HouseholdAddRequest:" in text
    assert "primary_card_number (required)" in text
    assert "new_member.name (required)" in text
    assert "validation: relationship note" in text


def test_question_bank_collection_for_events():
    text = format_question_collection(
        "request_library_event",
        heading="Collect details to populate EventRequest:",
        bullet_indent="  ",
    )

    assert "Collect details to populate EventRequest:" in text
    assert "event_type (required)" in text
    assert "desired_date (optional)" in text
    assert 'ask: "Roughly how many attendees do you expect?"' in text


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


def test_save_conversation_state_action_merges_partial_nested_updates():
    ctx = SimpleNamespace(state=State(value={}, delta={}))
    first = tools.ConversationStateUpdate(
        recommendation=tools.BookRecommendationRequest(
            patron=tools.PatronDetails(name="Joni Marsh"),
            favorite_genres=["fantasy"],
        )
    )
    tools.save_conversation_state_action(first, ctx)

    partial_update = {
        "recommendation": {
            "favorite_genres": ["thriller"],
            "mood": "spine-tingling",
        }
    }

    response = tools.save_conversation_state_action(partial_update, ctx)

    stored = ctx.state[tools.LIBRARY_STATE_KEY]
    assert stored["recommendation"]["patron"]["name"] == "Joni Marsh"
    assert stored["recommendation"]["favorite_genres"] == ["thriller"]
    assert stored["recommendation"]["mood"] == "spine-tingling"
    assert "recommendation" in response.applied_fields


def test_household_add_action_accepts_dict_payload():
    request_dict = {
        "primary_card_number": "CARD-9",
        "new_member": {"name": "Toby"},
    }

    response = tools.add_household_member_action(request_dict)

    assert response.confirmation_id.startswith("HH-")
    assert response.status in {"pending", "added"}


def test_request_event_action_accepts_dict_payload():
    request_dict = {
        "patron": {"name": "Jamie"},
        "event_type": "Book Club",
    }

    response = tools.request_event_action(request_dict)

    assert response.event_request_id.startswith("EVT-")
    assert response.status == "received"
