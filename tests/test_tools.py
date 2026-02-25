from datetime import datetime, timezone

import pytest

from app.tools import tools
from app.tools.requirements_helper import format_requirement_section


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
