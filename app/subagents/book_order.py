"""Book order agent configuration."""
from google.adk import Agent

from app.tools.question_bank import (
    format_confirmation_checklist,
    format_question_collection,
)
from app.tools.tools import order_book, save_conversation_state

COLLECTION_SECTION = format_question_collection(
    "order_book",
    heading="Collect details to populate BookOrderRequest:",
)
ROOT_REQUIREMENTS_SECTION = format_question_collection(
    "order_book",
    heading="- Book orders (BookOrderRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)
CONFIRMATION_SECTION = format_confirmation_checklist(
    "order_book",
    heading="Before using `order_book`, confirm:",
)
ROOT_CONFIRMATION_SECTION = format_confirmation_checklist(
    "order_book",
    heading="   Book order confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Require a clear yes before submitting.",
)
STATE_SAVE_INSTRUCTION = (
    "When book-order inputs are confirmed, call `save_conversation_state` with "
    "`book_order` filled out."
)


def create_agent(model) -> Agent:
    return Agent(
        name="book_order_agent",
        model=model,
        description="Places holds or purchase requests for titles the library will provide.",
        instruction=f"""
Use `order_book` to log a request for a specific title/format.
{COLLECTION_SECTION}
{STATE_SAVE_INSTRUCTION}
{CONFIRMATION_SECTION}
Confirm availability expectations (could be hold or purchase) and share the request_id plus next notification steps.
""",
        tools=[order_book, save_conversation_state],
    )
