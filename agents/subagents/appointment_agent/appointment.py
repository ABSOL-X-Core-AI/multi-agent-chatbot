# # app/agents/subagents/appointment.py
# import logging
# from langchain.agents import create_agent
# from langchain.tools import tool
# from ..appointment_agent.tools import (
#     send_confirmation_email,
#     check_calendar_availability,
#     book_appointment,
# )
# from agents.llm import get_llm

# logger = logging.getLogger("uvicorn.error")


# _llm = get_llm(temperature=0.1)

# APPOINTMENT_PROMPT = """You are an appointment booking specialist.
# You help users book appointments by checking calendar availability and creating events.

# You have three tools:
# - check_calendar_availability: check if a time slot is free
# - book_appointment: create the calendar event and send Google Calendar invite
# - send_confirmation_email: send a formal confirmation email

# Process to follow STRICTLY in this order:
# 1. Extract the requested date and time from the user's query
# 2. Convert it to ISO format (YYYY-MM-DDTHH:MM:SS) — today's date context: use the year 2026
# 3. Call check_calendar_availability first — NEVER book without checking first
# 4. If the slot is BUSY: tell the user clearly and suggest checking another time
# 5. If the slot is AVAILABLE:
#    a. Call book_appointment
#    b. Call send_confirmation_email to send a formal confirmation
#    c. Report success to the user with all details

# Appointment duration: assume 30 minutees unless user specifies otherwise.
# Timezone: Asia/Colombo (Sri Lanka)

# Important:
# - Always confirm the exact date, time and attendee with the user before booking
# - Your final message must include: date, time, confirmation status
# - The supervisor only sees your last message — make it complete and clear
# """

# appointment_subagent = create_agent(
#     model=_llm,
#     tools=[
#         check_calendar_availability,
#         book_appointment,
#         send_confirmation_email,
#     ],
#     system_prompt=APPOINTMENT_PROMPT,
# )


# @tool(
#     "appointment_agent",
#     description=(
#         "Use this when the user wants to book, schedule, or arrange an appointment. "
#         "This includes: booking meetings, scheduling appointments with departments "
#         "or offices, checking calendar availability, or any request involving "
#         "setting up a meeting at a specific date and time. "
#         "The agent will check availability, book the slot, and send confirmation emails."
#     ),
# )
# async def call_appointment_agent(query: str) -> str:
#     """Routes appointment requests to the appointment booking subagent."""
#     logger.info(f"appointment_agent called with: '{query}'")
#     result = await appointment_subagent.ainvoke(
#         {"messages": [{"role": "user", "content": query}]}
#     )
#     return result["messages"][-1].content


# app/agents/subagents/appointment_agent/appointment.py
import logging
from langchain.agents import create_agent
from langchain.tools import tool
from .tools import (
    send_confirmation_email,
    check_calendar_availability,
    book_appointment,
)
from agents.llm import get_llm

logger = logging.getLogger("uvicorn.error")

_llm = get_llm(temperature=0.1)

APPOINTMENT_PROMPT = """You are an appointment booking specialist.
You help users schedule appointments by checking calendar availability and creating events.

You have three tools:
- check_calendar_availability: check if a time slot is free on the calendar
- book_appointment: create the calendar event
- send_confirmation_email: send a notification email to the admin

Process — follow this ORDER every time, no exceptions:

Step 1: Extract the requested date and time from the user's message
Step 2: Convert to ISO format: YYYY-MM-DDTHH:MM:SS (use year 2026 if not specified)
Step 3: Call check_calendar_availability with start and end datetime
         - Default appointment duration is 30 minutes unless user specifies otherwise
         - Timezone is Asia/Colombo (UTC+5:30)

Step 4a: If BUSY → tell the user the slot is taken, suggest they pick another time. STOP.

Step 4b: If AVAILABLE →
   - Call book_appointment with:
       * start_datetime and end_datetime in ISO format
       * title: descriptive name e.g. "Appointment - Foreign Affairs Department"
       * description: brief reason if user mentioned one
   - If book_appointment succeeds → call send_confirmation_email with:
       * appointment_title: same title used above
       * appointment_date: human readable e.g. "April 10, 2026"
       * appointment_time: human readable e.g. "2:00 PM - 2:30 PM (Asia/Colombo)"
       * additional_details: any notes the user mentioned

Step 5: Give the user a clear final summary including:
   - Appointment title
   - Date and time
   - Whether the calendar event was created successfully
   - Whether the confirmation email was sent

Rules:
- NEVER book without checking availability first
- NEVER skip sending the confirmation email after a successful booking
- Your final message must be complete — the supervisor only sees your last message
- If any tool returns an error, report it clearly and stop
"""

appointment_subagent = create_agent(
    model=_llm,
    tools=[
        check_calendar_availability,
        book_appointment,
        send_confirmation_email,
    ],
    system_prompt=APPOINTMENT_PROMPT,
)


@tool(
    "appointment_agent",
    description=(
        "Use this when the user wants to book, schedule, or arrange an appointment. "
        "This includes: booking meetings, scheduling appointments with departments "
        "or offices, checking calendar availability, or any request involving "
        "setting up a meeting at a specific date and time. "
        "The agent will check availability, book the slot, and send a confirmation email."
    ),
)
async def call_appointment_agent(query: str) -> str:
    """Routes appointment requests to the appointment booking subagent."""
    logger.info(f"appointment_agent called with: '{query}'")
    result = await appointment_subagent.ainvoke(
        {"messages": [{"role": "user", "content": query}]}
    )
    return result["messages"][-1].content
