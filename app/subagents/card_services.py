"""Card services agent configuration."""
from google.adk import Agent

from app.tools.question_bank import (
    format_confirmation_checklist,
    format_question_collection,
)
from app.tools.tools import issue_library_card, save_conversation_state

COLLECTION_SECTION = format_question_collection(
    "issue_library_card",
    heading="Collect details to populate CardRequest:",
)
ROOT_REQUIREMENTS_SECTION = format_question_collection(
    "issue_library_card",
    heading="- New cards (CardRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)
CONFIRMATION_SECTION = format_confirmation_checklist(
    "issue_library_card",
    heading="Before using `issue_library_card`, confirm:",
)
ROOT_CONFIRMATION_SECTION = format_confirmation_checklist(
    "issue_library_card",
    heading="   Card enrollment confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Make sure they explicitly approve issuing the card.",
)
STATE_SAVE_INSTRUCTION = (
    "Persist card-enrollment details via `save_conversation_state` by passing "
    "a `card_request` object once confirmed."
)


def create_agent(_default_model) -> Agent:
    return Agent(
        name="card_services_agent",
        model="gemini-2.5-flash",
        description="Issues new library cards for individuals or households.",
        instruction=f"""
Use `issue_library_card` whenever a patron needs a new card.
{COLLECTION_SECTION}
{STATE_SAVE_INSTRUCTION}
{CONFIRMATION_SECTION}
Remind patrons that temporary PINs expire in 72 hours and explain pickup/verification requirements.
""",
        tools=[issue_library_card, save_conversation_state],
    )
