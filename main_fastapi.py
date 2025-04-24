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

def summarize_transcript(transcript: list) -> str:
    """Summarize a transcript using Azure OpenAI LLM."""
    logger.info("Summarizing transcript using Azure OpenAI LLM")
    try:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://rebootllm.openai.azure.com/")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        # If you need location or deployment name, adjust here
        deployment = "gpt-4o"  # Or fetch from env if needed
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2025-01-01-preview",
        )

        # Format transcript as a string
        transcript_text = "\n".join([
            f"{entry.get('speaker', 'Unknown')}: {entry.get('text', str(entry))}" if isinstance(entry, dict) else str(entry)
            for entry in transcript
        ])

        chat_prompt = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are an AI assistant that simply summarises call transcripts in a clear coherent way, keeping all the key points. Given a transcript, simply give a summary of the call and key points discussed. Secondly give feedback on the call to the user e.g. keep up the good work on x. Do the feedback in bullet points. ENSURE THE OUTPUT IS NO LONGER THAN 400 WORDS MAX, DO NOT GO ABOVE THIS LIMIT."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": transcript_text
                    }
                ]
            }
        ]

        completion = client.chat.completions.create(
            model=deployment,
            messages=chat_prompt,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False
        )
        # Extract the summary from the response
        summary = completion.choices[0].message.content if completion.choices else "No summary generated."
        return summary
    except Exception as e:
        logger.error(f"Error during transcript summarization: {e}")
        return "Error generating summary."

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
    return templates.TemplateResponse("index.html", {"request": request, "status_msg": status_msg, "call_status": call_status, "phone_input": phone_input, "poll_result": poll_result, "flash_message": flash_message, "flash_category": flash_category})

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

# Mount static directory for assets (if any exist)
# app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    uvicorn.run("main_fastapi:app", host="0.0.0.0", port=8000, reload=True)