"""Mock tools for the librarian tools."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from google.adk.sessions.state import State
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext


class PatronDetails(BaseModel):
    name: str = Field(..., description="Full name of the patron")
    card_number: Optional[str] = Field(
        default=None, description="Existing library card number if available"
    )
    contact_email: Optional[str] = Field(
        default=None, description="Primary email for notifications"
    )


class BookRecommendationRequest(BaseModel):
    patron: PatronDetails
    favorite_genres: list[str] = Field(
        default_factory=list,
        description="Genres the patron enjoys",
    )
    mood: Optional[str] = Field(
        default=None, description="Optional theme or reading mood"
    )
    recent_reads: list[str] = Field(
        default_factory=list, description="Recent titles the patron enjoyed"
    )


class BookRecommendationResponse(BaseModel):
    recommendations: list[str]
    generated_at: str = Field(
        description="ISO 8601 timestamp when recommendations were generated"
    )


class Address(BaseModel):
    street_line1: str
    street_line2: Optional[str] = Field(default=None)
    city: str
    state_or_province: str
    postal_code: str
    country: str = Field(default="USA")


class BookOrderRequest(BaseModel):
    patron: PatronDetails
    title: str
    author: Optional[str] = None
    format: Literal["hardcover", "paperback", "ebook", "audiobook"] = (
        "paperback"
    )
    shipping_address: Address = Field(
        ..., description="Destination for shipping or pickup confirmation"
    )
    preferred_vendor: str = Field(
        ..., description="Supplier or bookstore to source the title from"
    )
    preferred_vendor_address: Address = Field(
        ..., description="Business address of the preferred vendor"
    )
    needed_by: Optional[str] = Field(
        default=None,
        description=(
            "ISO 8601 date/time string for when the patron would like to "
            "receive the book (e.g., 2026-02-25T17:00:00Z)"
        ),
    )


class BookOrderResponse(BaseModel):
    request_id: str
    status: Literal["requested", "reserved", "backordered"]


class CardRequest(BaseModel):
    patron: PatronDetails
    household_members: list[PatronDetails] = Field(
        default_factory=list, description="Additional members for household cards"
    )


class CardResponse(BaseModel):
    card_number: str
    temporary_pin: str
    expires_at: str = Field(
        description="ISO 8601 timestamp when the temporary PIN expires"
    )


class EventRequest(BaseModel):
    patron: PatronDetails
    event_type: str = Field(
        ..., description="Type of event (e.g., book club, children's hour)"
    )
    desired_date: Optional[str] = Field(
        default=None,
        description=(
            "Preferred event date/time in ISO 8601 format "
            "(e.g., 2026-03-05T19:00:00Z)"
        ),
    )
    attendees: int = Field(default=1)
    special_requirements: Optional[str] = None


class EventResponse(BaseModel):
    event_request_id: str
    status: Literal["received", "scheduled", "waitlisted"]


class HouseholdAddRequest(BaseModel):
    primary_card_number: str
    new_member: PatronDetails
    relationship: Optional[str] = None


class HouseholdAddResponse(BaseModel):
    confirmation_id: str
    status: Literal["pending", "added"]


class ConversationState(BaseModel):
    """Stateful snapshot of patron-provided info."""

    recommendation: Optional[BookRecommendationRequest] = None
    book_order: Optional[BookOrderRequest] = None
    card_request: Optional[CardRequest] = None
    household_request: Optional[HouseholdAddRequest] = None
    event_request: Optional[EventRequest] = None
    last_confirmation_note: Optional[str] = Field(
        default=None,
        description="Summary of the last explicit confirmation from the patron",
    )


class ConversationStateUpdate(BaseModel):
    """Fields to upsert/clear in the conversation state."""

    recommendation: Optional[BookRecommendationRequest] = Field(
        default=None, description="Updated recommendation inputs"
    )
    book_order: Optional[BookOrderRequest] = Field(
        default=None, description="Updated book order inputs"
    )
    card_request: Optional[CardRequest] = Field(
        default=None, description="Updated card service inputs"
    )
    household_request: Optional[HouseholdAddRequest] = Field(
        default=None, description="Updated household linking inputs"
    )
    event_request: Optional[EventRequest] = Field(
        default=None, description="Updated programming/event inputs"
    )
    last_confirmation_note: Optional[str] = Field(
        default=None,
        description="Plain-language recap of what the patron approved",
    )


class ConversationStateResponse(BaseModel):
    state: ConversationState
    applied_fields: list[str] = Field(
        default_factory=list,
        description="State sections touched by this update",
    )


LIBRARY_STATE_KEY = f"{State.APP_PREFIX}library_conversation_state"


# Mock implementations -----------------------------------------------------


def _utc_iso(dt: datetime) -> str:
    """Return a timezone-aware UTC ISO 8601 string without microseconds."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def recommend_books_action(request: BookRecommendationRequest) -> BookRecommendationResponse:
    """Return a mock book recommendation list."""
    if isinstance(request, dict):
        request = BookRecommendationRequest(**request)
    fallback_titles = [
        "The Midnight Library",
        "Project Hail Mary",
        "Tomorrow, and Tomorrow, and Tomorrow",
    ]
    genre_hint = request.favorite_genres[0] if request.favorite_genres else "general"
    chosen = [f"{genre_hint.title()} Pick {i+1}" for i in range(2)] + fallback_titles
    return BookRecommendationResponse(
        recommendations=chosen[:5],
        generated_at=_utc_iso(datetime.now(timezone.utc)),
    )


def order_book_action(request: BookOrderRequest) -> BookOrderResponse:
    """Mock placing a book order."""
    if isinstance(request, dict):
        request = BookOrderRequest(**request)
    return BookOrderResponse(
        request_id=f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        status="requested",
    )


def issue_card_action(request: CardRequest) -> CardResponse:
    """Mock issuing a new card (primary plus optional household)."""
    if isinstance(request, dict):
        request = CardRequest(**request)
    now = datetime.now(timezone.utc)
    return CardResponse(
        card_number=f"CARD-{now.strftime('%H%M%S')}",
        temporary_pin="1234",
        expires_at=_utc_iso(now + timedelta(days=365 * 3)),
    )


def add_household_member_action(
    request: HouseholdAddRequest,
) -> HouseholdAddResponse:
    """Mock adding a person to an existing library card."""
    if isinstance(request, dict):
        request = HouseholdAddRequest(**request)
    return HouseholdAddResponse(
        confirmation_id=f"HH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
        status="added",
    )


def request_event_action(request: EventRequest) -> EventResponse:
    """Mock logging an event request."""
    if isinstance(request, dict):
        request = EventRequest(**request)
    return EventResponse(
        event_request_id=f"EVT-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        status="received",
    )


def _merge_values(base_value, update_value):
    if update_value is None:
        return None
    if isinstance(base_value, BaseModel):
        base_value = base_value.model_dump(exclude_none=False)
    if isinstance(update_value, BaseModel):
        update_value = update_value.model_dump(exclude_none=True)
    if isinstance(base_value, dict) and isinstance(update_value, dict):
        merged = dict(base_value)
        for key, value in update_value.items():
            merged[key] = _merge_values(merged.get(key), value)
        return merged
    return update_value


def _normalize_update_payload(update: ConversationStateUpdate | dict[str, Any]) -> dict[str, Any]:
    if isinstance(update, ConversationStateUpdate):
        return update.model_dump(exclude_none=True)
    normalized: dict[str, Any] = {}
    allowed_fields = set(ConversationStateUpdate.model_fields)
    for key, value in update.items():
        if key in allowed_fields:
            normalized[key] = value
    return normalized


def save_conversation_state_action(
    update: ConversationStateUpdate, tool_context: ToolContext
) -> ConversationStateResponse:
    """Persist patron-provided information to session state."""
    update_dict = _normalize_update_payload(update)
    if not update_dict:
        stored_value = tool_context.state.get(LIBRARY_STATE_KEY, {}) or {}
        current = (
            ConversationState.model_validate(stored_value)
            if stored_value
            else ConversationState()
        )
        return ConversationStateResponse(state=current, applied_fields=[])

    stored_value = tool_context.state.get(LIBRARY_STATE_KEY, {}) or {}
    current_state = (
        ConversationState.model_validate(stored_value)
        if stored_value
        else ConversationState()
    )
    merged_payload = current_state.model_dump(exclude_none=False)
    for field, value in update_dict.items():
        merged_payload[field] = _merge_values(merged_payload.get(field), value)

    merged_state = ConversationState.model_validate(merged_payload)
    tool_context.state[LIBRARY_STATE_KEY] = merged_state.model_dump(exclude_none=True)
    return ConversationStateResponse(
        state=merged_state, applied_fields=list(update_dict.keys())
    )


# Tools exposed to agents --------------------------------------------------
recommend_books = FunctionTool(recommend_books_action)
order_book = FunctionTool(order_book_action)
issue_library_card = FunctionTool(issue_card_action)
add_household_member = FunctionTool(add_household_member_action)
request_library_event = FunctionTool(request_event_action)
save_conversation_state = FunctionTool(save_conversation_state_action)
