import os
import logging
import smtplib
from dotenv import load_dotenv
from langchain.tools import tool
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()


logger = logging.getLogger("uvicorn.error")

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "agents/service_account_config/service-account.json"
)
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


def get_calendar_service():
    """Authenticate and return a Google Calendar service object."""
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds)


@tool
def check_calendar_availability(start_datetime: str, end_datetime: str) -> str:
    """
    Check if a time slot is available in the calendar.

    Args:
        start_datetime: Start time in ISO format e.g. '2026-04-10T14:00:00'
        end_datetime:   End time in ISO format   e.g. '2026-04-10T15:00:00'

    Returns:
        'available' or 'busy' with details of conflicting events.
    """
    try:
        service = get_calendar_service()

        # freebusy query checks for conflicts in the time range
        body = {
            "timeMin": start_datetime + "Z",  # Z = UTC
            "timeMax": end_datetime + "Z",
            "items": [{"id": CALENDAR_ID}],
        }

        result = service.freebusy().query(body=body).execute()
        busy_slots = result["calendars"][CALENDAR_ID]["busy"]

        if not busy_slots:
            return (
                f"available: The slot from {start_datetime} to {end_datetime} is free."
            )
        else:
            conflicts = [f"{s['start']} to {s['end']}" for s in busy_slots]
            return f"busy: Conflicting events found: {', '.join(conflicts)}"

    except Exception as e:
        logger.error(f"Calendar availability check failed: {e}")
        return f"error: Could not check availability — {str(e)}"


@tool
def book_appointment(
    start_datetime: str,
    end_datetime: str,
    title: str,
    description: str = "",
) -> str:
    """
    Create a Google Calendar event and send a notification via an email.

    Args:
        start_datetime:  ISO format e.g. '2026-04-10T14:00:00'
        end_datetime:    ISO format e.g. '2026-04-10T15:00:00'
        title:           Event title e.g. 'Appointment - Foreign Affairs Department'
        description:     Optional description of the appointment

    Returns:
        Confirmation message with event link and event ID.
    """
    try:
        service = get_calendar_service()

        event = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_datetime,
                "timeZone": "Asia/Colombo",
            },
            "end": {
                "dateTime": end_datetime,
                "timeZone": "Asia/Colombo",
            },
        }

        created_event = (
            service.events()
            .insert(
                calendarId=CALENDAR_ID,
                body=event,
            )
            .execute()
        )

        event_id = created_event.get("id", "")
        event_link = created_event.get("htmlLink", "")

        logger.info(f"Event created: {event_id}")
        return (
            f"success: Appointment '{title}' booked successfully.\n"
            f"Date: {start_datetime} to {end_datetime}\n"
            f"Event ID: {event_id}"
            f"Event link: {event_link}\n"
        )

    except Exception as e:
        logger.error(f"Booking failed: {e}")
        return f"error: Could not book appointment — {str(e)}"


# @tool
# def send_confirmation_email(
#     to_email: str,
#     subject: str,
#     body: str,
# ) -> str:
#     """
#     Send a confirmation email about the appointment.
#     Use this AFTER booking to send a formal confirmation email.

#     Args:
#         to_email: Recipient email address
#         subject:  Email subject line
#         body:     Email body text (plain text)

#     Returns:
#         Confirmation that email was sent.
#     """
#     try:
#         msg = MIMEMultipart()
#         msg["From"] = SENDER_EMAIL
#         msg["To"] = to_email
#         msg["Subject"] = subject
#         msg.attach(MIMEText(body, "plain"))

#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(SENDER_EMAIL, EMAIL_PASSWORD)
#             server.send_message(msg)

#         logger.info(f"Confirmation email sent to {to_email}")
#         return f"success: Confirmation email sent to {to_email}"

#     except Exception as e:
#         logger.error(f"Email sending failed: {e}")
#         return f"error: Could not send email — {str(e)}"


@tool
def send_confirmation_email(
    appointment_title: str,
    appointment_date: str,
    appointment_time: str,
    additional_details: str = "",
) -> str:
    """
    Send a confirmation email to the admin after an appointment is booked.
    Always call this AFTER book_appointment succeeds.

    Args:
        appointment_title:   Title of the appointment e.g. 'Appointment - Foreign Affairs'
        appointment_date:    Human readable date e.g. 'April 10, 2026'
        appointment_time:    Human readable time e.g. '2:00 PM - 3:00 PM'
        additional_details:  Any extra notes about the appointment

    Returns:
        Confirmation that email was sent or error message.
    """
    try:
        if not SENDER_EMAIL or not EMAIL_PASSWORD:
            return "error: SENDER_EMAIL or EMAIL_PASSWORD not set in environment."

        if not RECEIVER_EMAIL:
            return "error: RECEIVER_EMAIL not set in environment."

        subject = f"New Appointment Booked: {appointment_title}"

        body = f"""Hello,

A new appointment has been successfully booked via the chatbot.

Appointment Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title  : {appointment_title}
Date   : {appointment_date}
Time   : {appointment_time}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{f"Additional details: {additional_details}" if additional_details else ""}

This appointment has been added to your Google Calendar (appointment-calendar).
Please check your calendar for full details.

This is an automated notification from your AI Assistant.
"""

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Confirmation email sent to {RECEIVER_EMAIL}")
        return f"success: Confirmation email sent to {RECEIVER_EMAIL}"

    except smtplib.SMTPAuthenticationError:
        return (
            "error: Gmail authentication failed. "
            "Make sure you are using a Gmail App Password, not your regular password. "
            "Go to Google Account → Security → 2-Step Verification → App Passwords."
        )
    except Exception as e:
        logger.error(f"Email failed: {e}")
        return f"error: Could not send email — {str(e)}"
