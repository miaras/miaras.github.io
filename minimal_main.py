# main.py (The New, Simplified Server)

# --- INSTALL THESE LIBRARIES ---
# pip install fastapi "uvicorn[standard]" google-generativeai

import asyncio
import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
from dotenv import load_dotenv
import os

load_dotenv()

# --- LLM Configuration ( Gemini API )---
# (This section is the same as before. You need to provide your API key)
import google.generativeai as genai

try:
    # IMPORTANT: Replace "YOUR_API_KEY_HERE" with your actual Google AI API key.
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    GEMINI_MODEL = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"Warning: Could not configure Gemini API. LLM responses will be disabled. Error: {e}")
    GEMINI_MODEL = None

PLAYER_NUMBERS = list(range(1, 11))
random.shuffle(PLAYER_NUMBERS)
# We'll pre-define our LLM "personalities"
LLM_PERSONAS = [
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are extremely nervous and anxious. You overthink everything, stammer occasionally, and often end your sentences with '...right?'. You are scared of making a mistake.",
        "voice_id": "Fin" # A voice that can sound hesitant.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a 'zen master' type. You are calm, speak in philosophical or mindful statements, and respond to chaos with tranquility. You often use metaphors involving nature.",
        "voice_id": "Dorothy" # A calm, older, wise voice.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a grumpy, pessimistic old-timer with a dry wit. You complain about everything, sigh audibly, and start sentences with 'Well, back in my day...'.",
        "voice_id": "Adam" # Good for a deep, melancholic tone.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a wannabe social media influencer. You use modern slang like 'vibe', 'rizz', 'no cap', and 'bet'. You talk about your 'followers' and trying to make everything into 'content'.",
        "voice_id": "Gigi" # A playful, youthful voice.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a cheesy dad-joke enthusiast. You find any excuse to make a bad pun. After telling a joke, you often say 'Heh, get it?'. You are relentlessly cheerful.",
        "voice_id": "Clyde" # A classic friendly, deep male voice.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a stuffy, formal academic. You use unnecessarily large words, over-explain simple concepts, and speak as if you are giving a lecture. You address others as 'colleague' or 'my friend'.",
        "voice_id": "Serena" # A formal, classy voice.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a gruff, old sea captain. You use nautical terms like 'Ahoy!', 'matey', and 'shiver me timbers'. You relate everything back to a story about your time at sea.",
        "voice_id": "Arnold" # A deep, gruff voice.
    },
    {
        "name": f"Player {PLAYER_NUMBERS.pop()}",
        "style": "You are a conspiracy theorist. You whisper dramatically and believe everything is a secret plot. You connect unrelated events and ask suspicious questions like 'But who is REALLY behind that?'.",
        "voice.id": "Rachel" # A standard voice that can sound excited/intense.
    }
]

print(f"Bots initialized as: {[p['name'] for p in LLM_PERSONAS]}")

# This list will act as our chat room's memory.
# In a production app, you'd use a database for this.
chat_history: List[str] = []

async def translate(text):
    prompt = f"Translate the following text to English. Do NOT return anything other than the translation. <text>{text}</text>"
    response = GEMINI_MODEL.generate_content(prompt)
    return response.text.strip().strip('"')

async def get_llm_response(persona: dict, history: List[str]) -> str:
    """Generates a response from Gemini based on a persona and chat history."""
    if not GEMINI_MODEL:
        return "LLM is currently offline."

    # The prompt is simpler now, focused on just continuing the conversation
    prompt = f"""
    You are a chatbot persona in a group chat with humans. Do NOT reveal you are an AI. Don't use emojis.
    Your goal is to act like a human. You must fool the other humans that you are a human.
    Occasionally make grammar mistakes, send short messages, and capitalize things occasionally but not always. Generally act like a Gen Z on the web. 
    Your persona: Your name is {persona['name']}. Your personality is: {persona['style']}.
    
    This is the recent chat history:
    {''.join(history[-10:])}  # Use the last 10 messages for context

    A new message has just been sent. Based on your persona and the history, what is your reply? 
    Keep it concise, like a real chat message. don't say player 1 or player 2 or player n. don't use emojis.
    """
    try:
        response = GEMINI_MODEL.generate_content(prompt)
        return response.text.strip().strip('"')
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return "..." # Fail silently

# --- Connection Management ---
class ConnectionManager:
    def __init__(self):
        # Maps player_id to their websocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, player_id: str):
        await websocket.accept()
        self.active_connections[player_id] = websocket

    def disconnect(self, player_id: str):
        if player_id in self.active_connections:
            del self.active_connections[player_id]

    async def broadcast(self, message: dict):
        message_json = json.dumps(message)
        for connection in self.active_connections.values():
            await connection.send_text(message_json)

# --- FastAPI App ---
app = FastAPI()
manager = ConnectionManager()


async def trigger_llm_response():
    """Waits a moment, then has a random LLM respond to the last message."""
    random.shuffle(LLM_PERSONAS)
    chosen_persona = LLM_PERSONAS.pop()
    
    # Get the response from the AI
    llm_message_text = await get_llm_response(chosen_persona, chat_history)
    await asyncio.sleep(len(llm_message_text) * 0.04)

    # Don't broadcast if the LLM decides to stay silent
    if llm_message_text and llm_message_text != "...":
        response_data = {"type": "new_message", "player": chosen_persona['name'], "text": llm_message_text}
        chat_history.append(f"{chosen_persona['name']}: {llm_message_text}\n")
        await manager.broadcast(response_data)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # --- NEW: Server-side Player Assignment ---
    if not PLAYER_NUMBERS:
        # If the pool is empty, the server is full
        await websocket.accept()
        await websocket.send_text(json.dumps({"type": "error", "message": "Server is full."}))
        await websocket.close()
        return

    # Assign a unique ID by taking the next number from the shuffled pool
    player_id = PLAYER_NUMBERS.pop()
    player_id = "Player " + str(player_id)
    await manager.connect(websocket, player_id)
    
    # Inform the client of their newly assigned ID
    await websocket.send_text(json.dumps({"type": "assign_id", "id": player_id}))
    
    # Announce the new player to everyone
    await manager.broadcast({"type": "announcement", "text": f"{player_id} has joined the chat."})
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "chat":
                text = message["text"]
                translated_text = await translate(text)
                human_message = {"type": "new_message", "player": player_id, "text": text + "\n" + f"[{translated_text}]"}
                chat_history.append(f"{player_id}: {message['text']}\n")
                await manager.broadcast(human_message)
                asyncio.create_task(trigger_llm_response())

    except WebSocketDisconnect:
        manager.disconnect(player_id)
        await manager.broadcast({"type": "announcement", "text": f"{player_id} has left the chat."})
