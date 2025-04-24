import os
import time
import json
import logging
import datetime
from fastapi import FastAPI, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from requests.auth import HTTPBasicAuth
import base64
from openai import AzureOpenAI
import uvicorn
from typing import Dict

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

AGENT_ID = os.getenv("AGENT_ID")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_PHONE_NUMBER_ID = os.getenv("AGENT_PHONE_NUMBER_ID")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger("main_fastapi")

def format_uk_number(number: str) -> str:
    """Format a UK phone number to E.164 format for Twilio.

    Args:
        number (str): The input phone number (local or international).

    Returns:
        str: The formatted phone number.
    """
    if number.startswith("0") and len(number) == 11:
        return "+44" + number[1:]
    elif number.startswith("+44"):
        return number
    return number

def get_call_status(account_sid: str, auth_token: str, call_sid: str) -> str:
    """Query Twilio for the status of a call.

    Args:
        account_sid (str): Twilio account SID.
        auth_token (str): Twilio auth token.
        call_sid (str): The SID of the call.

    Returns:
        str: The status of the call, or None if error.
    """
    import requests
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
    resp = requests.get(url, auth=HTTPBasicAuth(account_sid, auth_token))
    if resp.status_code == 200:
        logger.debug(f"Fetched call status for {call_sid}: {resp.json().get('status')}")
        return resp.json().get("status")
    logger.error(f"Twilio status fetch error: {resp.status_code} {resp.text}")
    return None

def get_conversation_data(conversation_id: str):
    """Return conversation details as dict/model for internal use."""
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    detail = client.conversational_ai.get_conversation(conversation_id=conversation_id)
    if hasattr(detail, 'dict'):
        return detail.dict()
    if hasattr(detail, '__dict__'):
        return dict(detail.__dict__)
    return detail

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page with form for outbound call initiation."""
    return templates.TemplateResponse("index.html", {"request": request, "status_msg": None, "call_status": None, "phone_input": "", "flash_message": None, "flash_category": None})

@app.post("/call", response_class=HTMLResponse)
async def make_call(request: Request):
    """Initiate an outbound call, poll for status, and store summary in knowledge base.

    Args:
        request (Request): The incoming request object.
        phone_number (str): The phone number to call.

    Returns:
        HTMLResponse: Rendered template with call status and messages.
    """
    status_msg = None
    call_status = None

    body = await request.body()
    data = json.loads(body)
    phone_input = data.get("phone_number", "").strip()

    to_number = format_uk_number(phone_input)
    logger.info(f"Initiating outbound call to {to_number}")
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    flash_message = None
    flash_category = None
    try:
        response = client.conversational_ai.twilio_outbound_call(
            agent_id=AGENT_ID,
            agent_phone_number_id=AGENT_PHONE_NUMBER_ID,
            to_number=to_number,
        )
    except Exception as e:
        logger.error(f"Error initiating call: {e}")
        flash_message = f"Error initiating call: {e}"
        flash_category = "error"
        return templates.TemplateResponse("index.html", {"request": request, "status_msg": None, "call_status": None, "phone_input": phone_input, "flash_message": flash_message, "flash_category": flash_category})
    call_sid = None
    if isinstance(response, dict):
        call_sid = response.get("call_sid")
        status_msg = response.get("message")
    else:
        call_sid = getattr(response, "call_sid", None)
        status_msg = getattr(response, "message", None)
    logger.info(f"API Response: {status_msg}, call_sid: {call_sid}")
    poll_result = []
    if call_sid and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        logger.info(f"Waiting for call {call_sid} to complete...")
        for _ in range(12):
            status = get_call_status(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, call_sid)
            poll_result.append(status)
            logger.info(f"Current call status: {status}")
            if status in ("completed", "failed", "busy", "no-answer", "canceled"):
                break
            time.sleep(5)
        call_status = status
    else:
        logger.warning("No call_sid or Twilio credentials available for status polling.")
        call_status = "No call_sid or Twilio credentials available."
    # Summarize transcript and add to knowledge base
    try:
        convs = client.conversational_ai.get_conversations(agent_id=AGENT_ID)
        if convs.conversations:
            latest = convs.conversations[-1]
            detail = client.conversational_ai.get_conversation(conversation_id=latest.conversation_id)
            transcript = detail.transcript or []
            summary = summarize_transcript(transcript)
            timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
            transcript_lines = []
            for idx, msg in enumerate(transcript, 1):
                role = msg.get('role', '?')
                t = msg.get('time_in_call_secs', '?')
                text = msg.get('message', '')
                transcript_lines.append(f"{idx}. [{role}, {t}s]: {text}")
            doc_text = f"""Date: {timestamp}\nConversation ID: {latest.conversation_id}\nSummary: {summary}\nTranscript:\n""" + "\n".join(transcript_lines)
            client.conversational_ai.create_knowledge_base_text_document(text=doc_text)
            logger.info(f"Saved transcript summary for conversation {latest.conversation_id}")
    except Exception as e:
        logger.error(f"Error saving transcript summary: {e}")
    return JSONResponse(content=json.dumps({"status_msg": status_msg, "call_status": call_status, "phone_input": phone_input, "poll_result": poll_result, "flash_message": flash_message, "flash_category": flash_category}))

@app.get("/conversations")
async def get_conversations():
    """Return a list of conversations for the agent."""
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    try:
        result = client.conversational_ai.get_conversations(agent_id=AGENT_ID)
        logger.debug("Fetched conversations list.")
        return JSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        return JSONResponse(content={"conversations": [], "error": str(e)}, status_code=500)

@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Return details for a specific conversation.

    Args:
        conversation_id (str): The ID of the conversation.

    Returns:
        JSONResponse: The conversation details or error.
    """
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    try:
        result = client.conversational_ai.get_conversation(conversation_id=conversation_id)
        logger.debug(f"Fetched conversation details for {conversation_id}")
        return JSONResponse(content=result.dict())
    except Exception as e:
        logger.error(f"Error fetching conversation details: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/latest_transcript_summary", response_class=JSONResponse)
async def latest_transcript_summary() -> JSONResponse:
    """Return the most recent conversation summary in JSON format, matching the logic in simple_transcript_summary.py."""
    api_key = os.environ["ELEVENLABS_API_KEY"]
    client = ElevenLabs(api_key=api_key)

    result = client.conversational_ai.get_conversations(agent_id=AGENT_ID)
    conversations = result.conversations

    if not conversations:
        return JSONResponse(content={"error": "No conversations found."}, status_code=404)

    for convo in conversations:
        convo_full = client.conversational_ai.get_conversation(conversation_id=convo.conversation_id)
        transcript = convo_full.analysis.transcript_summary
        use_transcript = transcript != "Summary couldn't be generated for this call."

        if convo.call_duration_secs >= 10 and use_transcript:
            dt = datetime.datetime.fromtimestamp(convo.start_time_unix_secs)
            convo_details: Dict = {
                "time": dt.isoformat(),
                "conversation_id": convo.conversation_id,
                "duration_seconds": convo.call_duration_secs,
                "transcript_summary": convo_full.analysis.transcript_summary
            }
            return JSONResponse(content=convo_details)
    return JSONResponse(content={"error": "No matching conversation found."}, status_code=404)

# Mount static directory for assets (if any exist)
# app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run("main_fastapi:app", host="0.0.0.0", port=8000, reload=True)