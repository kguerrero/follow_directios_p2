"""Household link agent configuration."""
from google.adk import Agent

from app.tools.question_bank import (
    format_confirmation_checklist,
    format_question_collection,
)
from app.tools.tools import add_household_member, save_conversation_state

COLLECTION_SECTION = format_question_collection(
    "add_household_member",
    heading="Collect details to populate HouseholdAddRequest:",
)
ROOT_REQUIREMENTS_SECTION = format_question_collection(
    "add_household_member",
    heading="- Household additions (HouseholdAddRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)
CONFIRMATION_SECTION = format_confirmation_checklist(
    "add_household_member",
    heading="Before using `add_household_member`, confirm:",
)
ROOT_CONFIRMATION_SECTION = format_confirmation_checklist(
    "add_household_member",
    heading="   Household addition confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Confirm the primary cardholder authorizes the change.",
)
STATE_SAVE_INSTRUCTION = (
    "Store household-linking info with `save_conversation_state` under the "
    "`household_request` field after approval."
)


def create_agent(model) -> Agent:
    return Agent(
        name="household_link_agent",
        model=model,
        description="Adds an additional reader to an existing library account.",
        instruction=f"""
Call `add_household_member` to attach someone to an existing library card.
{COLLECTION_SECTION}
{STATE_SAVE_INSTRUCTION}
{CONFIRMATION_SECTION}
Confirm that the primary cardholder approves the addition and summarize any pending ID checks.
""",
        tools=[add_household_member, save_conversation_state],
    )
