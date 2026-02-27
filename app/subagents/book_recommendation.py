"""Book recommendation specialist agent."""
from google.adk import Agent

from app.tools.question_bank import (
    format_confirmation_checklist,
    format_question_collection,
)
from app.tools.tools import recommend_books, save_conversation_state

COLLECTION_SECTION = format_question_collection(
    "recommend_books",
    heading="Collect details to populate BookRecommendationRequest:",
)
ROOT_REQUIREMENTS_SECTION = format_question_collection(
    "recommend_books",
    heading="- Recommendations (BookRecommendationRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)
CONFIRMATION_SECTION = format_confirmation_checklist(
    "recommend_books",
    heading="Before using `recommend_books`, confirm:",
)
ROOT_CONFIRMATION_SECTION = format_confirmation_checklist(
    "recommend_books",
    heading="   Recommendations confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Require the patron to affirm accuracy before routing.",
)
STATE_SAVE_INSTRUCTION = (
    "After the patron approves the plan, call `save_conversation_state` with "
    "the `recommendation` field set to the BookRecommendationRequest payload, "
    "so peers can reuse it."
)


def create_agent(model) -> Agent:
    return Agent(
        name="book_recommendation_agent",
        model=model,
        description="Curates personalized reading lists for patrons.",
        instruction=f"""
Primary action: call `recommend_books` once per patron request.
{COLLECTION_SECTION}
{STATE_SAVE_INSTRUCTION}
{CONFIRMATION_SECTION}
Map conversation data into the BookRecommendationRequest schema before invoking the tool.
After receiving results, explain the suggestions, cite any follow-up actions (holds, waitlists), and invite feedback.
""",
        tools=[recommend_books, save_conversation_state],
    )
