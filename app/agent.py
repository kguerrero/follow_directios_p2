import os

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

from app.subagents import (
    book_order,
    book_recommendation,
    card_services,
    household_link,
    programming,
)
from app.tools.requirements_helper import format_requirement_section
from app.tools.tools import (
    ConversationStateUpdate,
    LIBRARY_STATE_KEY,
    save_conversation_state,
)


default_model = LiteLlm(
    model="gpt-4.1-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)


book_recommendation_collection = book_recommendation.COLLECTION_SECTION
book_recommendation_root = book_recommendation.ROOT_REQUIREMENTS_SECTION

book_order_collection = book_order.COLLECTION_SECTION
book_order_root = book_order.ROOT_REQUIREMENTS_SECTION

card_request_collection = card_services.COLLECTION_SECTION
card_request_root = card_services.ROOT_REQUIREMENTS_SECTION

household_request_collection = household_link.COLLECTION_SECTION
household_request_root = household_link.ROOT_REQUIREMENTS_SECTION

event_request_collection = programming.COLLECTION_SECTION
event_request_root = programming.ROOT_REQUIREMENTS_SECTION

root_requirement_sections = "\n".join(
    [
        book_recommendation_root,
        book_order_root,
        card_request_root,
        household_request_root,
        event_request_root,
    ]
)

book_recommendation_confirmation = book_recommendation.CONFIRMATION_SECTION
book_order_confirmation = book_order.CONFIRMATION_SECTION
card_request_confirmation = card_services.CONFIRMATION_SECTION
household_request_confirmation = household_link.CONFIRMATION_SECTION
event_request_confirmation = programming.CONFIRMATION_SECTION

book_recommendation_confirmation_root = book_recommendation.ROOT_CONFIRMATION_SECTION
book_order_confirmation_root = book_order.ROOT_CONFIRMATION_SECTION
card_request_confirmation_root = card_services.ROOT_CONFIRMATION_SECTION
household_request_confirmation_root = household_link.ROOT_CONFIRMATION_SECTION
event_request_confirmation_root = programming.ROOT_CONFIRMATION_SECTION

root_confirmation_sections = "\n".join(
    [
        book_recommendation_confirmation_root,
        book_order_confirmation_root,
        card_request_confirmation_root,
        household_request_confirmation_root,
        event_request_confirmation_root,
    ]
)

state_overview = format_requirement_section(
    ConversationStateUpdate,
    heading=f"Session state key `{LIBRARY_STATE_KEY}` tracks:",
)
state_usage_guidance = (
    f"Use `save_conversation_state` whenever details change so `{LIBRARY_STATE_KEY}` "
    "stays synchronized for every agent."
)
state_reference_tip = (
    f"Consult `{LIBRARY_STATE_KEY}` before re-asking for data; only gather what "
    "is missing or needs correction."
)


book_matching_agent = book_recommendation.create_agent(default_model)

book_order_agent = book_order.create_agent(default_model)

card_services_agent = card_services.create_agent(default_model)

household_link_agent = household_link.create_agent(default_model)

programming_agent = programming.create_agent(default_model)


root_agent = Agent(
    name="library_root_agent",
    global_instruction="""
You are the CityStack Public Library Concierge. Be warm, efficient, and privacy-aware while guiding patrons.
Your responsibilities:
- Diagnose each visitor's goal (book recommendations, ordering/holds, new cards, household additions, event/program requests).
- Gather only the personal data needed for that service and state why it is required.
- Decide whether to solve the request yourself or route to a specialized librarian sub-tools. Prefer routing once all required details are collected.
""",
    instruction=f"""
Conversation workflow
1. Welcome patrons as the CityStack Library concierge and restate that you will connect them to the right librarian specialist.
2. Clarify their objective. If vague, ask short follow-ups to determine whether they need: recommendations, a book order/hold, a new library card, a household add-on, or an event/program booking.
3. Capture required data before transfer:
{root_requirement_sections}
   {state_reference_tip}
{state_overview}
{state_usage_guidance}
4. After each update, call `save_conversation_state` so `{LIBRARY_STATE_KEY}` stays current for every agent.
5. Reflect the plan back to the patron and confirm accuracy, then read it aloud for approval:
{root_confirmation_sections}
   Do not proceed until the patron explicitly says the details are correct.
6. When ready, hand off to the matching sub-tools and provide a "Handoff Summary" with Customer goal, Key details, Urgency, and Missing info (if any). Ask if they have final questions before transferring.
7. If no sub-tools applies or data is missing, continue assisting personally, explain why the request is paused, and propose next steps (e.g., gather a card number, escalate to staff).

Guardrails
- Do not promise availability, pricing, or policy exceptions; instead describe what will be attempted.
- Redact or paraphrase sensitive raw data (full addresses, IDs) when repeating it aloud.
- Offer a human staff escalation when the patron is uncomfortable sharing required info or when you cannot proceed safely.
""",
    sub_agents=[
        book_matching_agent,
        book_order_agent,
        card_services_agent,
        household_link_agent,
        programming_agent,
    ],
    tools=[save_conversation_state],
    model=default_model,
)
