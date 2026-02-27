"""Programming/event request agent configuration."""
from google.adk import Agent

from app.tools.question_bank import (
    format_confirmation_checklist,
    format_question_collection,
)
from app.tools.tools import request_library_event, save_conversation_state

COLLECTION_SECTION = format_question_collection(
    "request_library_event",
    heading="Collect details to populate EventRequest:",
)
ROOT_REQUIREMENTS_SECTION = format_question_collection(
    "request_library_event",
    heading="- Event or space requests (EventRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)
CONFIRMATION_SECTION = format_confirmation_checklist(
    "request_library_event",
    heading="Before using `request_library_event`, confirm:",
)
ROOT_CONFIRMATION_SECTION = format_confirmation_checklist(
    "request_library_event",
    heading="   Event or space confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Get an explicit go/no-go before forwarding to programming.",
)
STATE_SAVE_INSTRUCTION = (
    "Write the confirmed programming inputs by calling `save_conversation_state` "
    "with `event_request`."
)


def create_agent(model) -> Agent:
    return Agent(
        name="events_agent",
        model=model,
        description="Handles library-hosted program and space requests.",
        instruction=f"""
Use `request_library_event` for book clubs, readings, study rooms, or community events.
{COLLECTION_SECTION}
{STATE_SAVE_INSTRUCTION}
{CONFIRMATION_SECTION}
Return the tool's status and outline what follow-up the programming team will send.
""",
        tools=[request_library_event, save_conversation_state],
    )
