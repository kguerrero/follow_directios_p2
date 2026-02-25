import os

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

from app.tools.requirements_helper import (
    format_confirmation_prompt,
    format_requirement_section,
)
from app.tools.tools import (
    BookRecommendationRequest,
    BookOrderRequest,
    CardRequest,
    ConversationStateUpdate,
    EventRequest,
    HouseholdAddRequest,
    LIBRARY_STATE_KEY,
    add_household_member,
    issue_library_card,
    order_book,
    recommend_books,
    request_library_event,
    save_conversation_state,
)


default_model = LiteLlm(
    model="gpt-4.1-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)


book_recommendation_collection = format_requirement_section(
    BookRecommendationRequest,
    heading="Collect details to populate BookRecommendationRequest:",
)
book_recommendation_root = format_requirement_section(
    BookRecommendationRequest,
    heading="- Recommendations (BookRecommendationRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)

book_order_collection = format_requirement_section(
    BookOrderRequest,
    heading="Collect details to populate BookOrderRequest:",
)
book_order_root = format_requirement_section(
    BookOrderRequest,
    heading="- Book orders (BookOrderRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)

card_request_collection = format_requirement_section(
    CardRequest,
    heading="Collect details to populate CardRequest:",
)
card_request_root = format_requirement_section(
    CardRequest,
    heading="- New cards (CardRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)

household_request_collection = format_requirement_section(
    HouseholdAddRequest,
    heading="Collect details to populate HouseholdAddRequest:",
)
household_request_root = format_requirement_section(
    HouseholdAddRequest,
    heading="- Household additions (HouseholdAddRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)

event_request_collection = format_requirement_section(
    EventRequest,
    heading="Collect details to populate EventRequest:",
)
event_request_root = format_requirement_section(
    EventRequest,
    heading="- Event or space requests (EventRequest):",
    heading_indent="   ",
    bullet_indent="     ",
)

root_requirement_sections = "\n".join(
    [
        book_recommendation_root,
        book_order_root,
        card_request_root,
        household_request_root,
        event_request_root,
    ]
)

book_recommendation_confirmation = format_confirmation_prompt(
    BookRecommendationRequest,
    heading="Before using `recommend_books`, confirm:",
)
book_order_confirmation = format_confirmation_prompt(
    BookOrderRequest,
    heading="Before using `order_book`, confirm:",
)
card_request_confirmation = format_confirmation_prompt(
    CardRequest,
    heading="Before using `issue_library_card`, confirm:",
)
household_request_confirmation = format_confirmation_prompt(
    HouseholdAddRequest,
    heading="Before using `add_household_member`, confirm:",
)
event_request_confirmation = format_confirmation_prompt(
    EventRequest,
    heading="Before using `request_library_event`, confirm:",
)

book_recommendation_confirmation_root = format_confirmation_prompt(
    BookRecommendationRequest,
    heading="   Recommendations confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Require the patron to affirm accuracy before routing.",
)
book_order_confirmation_root = format_confirmation_prompt(
    BookOrderRequest,
    heading="   Book order confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Require a clear yes before submitting.",
)
card_request_confirmation_root = format_confirmation_prompt(
    CardRequest,
    heading="   Card enrollment confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Make sure they explicitly approve issuing the card.",
)
household_request_confirmation_root = format_confirmation_prompt(
    HouseholdAddRequest,
    heading="   Household addition confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Confirm the primary cardholder authorizes the change.",
)
event_request_confirmation_root = format_confirmation_prompt(
    EventRequest,
    heading="   Event or space confirmation checklist:",
    bullet_indent="     ",
    closing_line="   Get an explicit go/no-go before forwarding to programming.",
)

root_confirmation_sections = "\n".join(
    [
        book_recommendation_confirmation_root,
        book_order_confirmation_root,
        card_request_confirmation_root,
        household_request_confirmation_root,
        event_request_confirmation_root,
    ]
)

book_recommendation_state_save = (
    "After the patron approves the plan, call `save_conversation_state` with "
    "the `recommendation` field set to the BookRecommendationRequest payload, "
    "so peers can reuse it."
)
book_order_state_save = (
    "When book-order inputs are confirmed, call `save_conversation_state` with "
    "`book_order` filled out."
)
card_request_state_save = (
    "Persist card-enrollment details via `save_conversation_state` by passing "
    "a `card_request` object once confirmed."
)
household_request_state_save = (
    "Store household-linking info with `save_conversation_state` under the "
    "`household_request` field after approval."
)
event_request_state_save = (
    "Write the confirmed programming inputs by calling `save_conversation_state` "
    "with `event_request`."
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


book_matching_agent = Agent(
    name="book_recommendation_agent",
    model=default_model,
    description="Curates personalized reading lists for patrons.",
    instruction=f"""
Primary action: call `recommend_books` once per patron request.
{book_recommendation_collection}
{book_recommendation_state_save}
{book_recommendation_confirmation}
Map conversation data into the BookRecommendationRequest schema before invoking the tool.
After receiving results, explain the suggestions, cite any follow-up actions (holds, waitlists), and invite feedback.
""",
    tools=[recommend_books, save_conversation_state],
)


book_order_agent = Agent(
    name="book_order_agent",
    model=default_model,
    description="Places holds or purchase requests for titles the library will provide.",
    instruction=f"""
Use `order_book` to log a request for a specific title/format.
{book_order_collection}
{book_order_state_save}
{book_order_confirmation}
Confirm availability expectations (could be hold or purchase) and share the request_id plus next notification steps.
""",
    tools=[order_book, save_conversation_state],
)


card_services_agent = Agent(
    name="card_services_agent",
    model="gemini-2.5-flash",
    description="Issues new library cards for individuals or households.",
    instruction=f"""
Use `issue_library_card` whenever a patron needs a new card.
{card_request_collection}
{card_request_state_save}
{card_request_confirmation}
Remind patrons that temporary PINs expire in 72 hours and explain pickup/verification requirements.
""",
    tools=[issue_library_card, save_conversation_state],
)


household_link_agent = Agent(
    name="household_link_agent",
    model=default_model,
    description="Adds an additional reader to an existing library account.",
    instruction=f"""
Call `add_household_member` to attach someone to an existing library card.
{household_request_collection}
{household_request_state_save}
{household_request_confirmation}
Confirm that the primary cardholder approves the addition and summarize any pending ID checks.
""",
    tools=[add_household_member, save_conversation_state],
)


programming_agent = Agent(
    name="events_agent",
    model=default_model,
    description="Handles library-hosted program and space requests.",
    instruction=f"""
Use `request_library_event` for book clubs, readings, study rooms, or community events.
{event_request_collection}
{event_request_state_save}
{event_request_confirmation}
Return the tool's status and outline what follow-up the programming team will send.
""",
    tools=[request_library_event, save_conversation_state],
)


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
