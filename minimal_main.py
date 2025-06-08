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

def create_random_name():
    """Creates a random name using unexpected adjective and noun combinations."""
    adjectives = [
        "Suspicious", "Melting", "Backwards", "Invisible", "Floating", "Twisted", "Magnetic", 
        "Frozen", "Glowing", "Whispering", "Dancing", "Shimmering", "Crumbling", "Elastic",
        "Bitter", "Sleepy", "Anxious", "Dizzy", "Clumsy", "Grumpy", "Jolly", "Sneaky",
        "Wobbly", "Spicy", "Fuzzy", "Sticky", "Bouncy", "Squiggly", "Sparkly", "Musty",
        "Crispy", "Sloppy", "Chunky", "Silky", "Rusty", "Dusty", "Misty", "Crusty"
    ]
    
    nouns = [
        "Banana", "Trombone", "Shoelace", "Paperclip", "Doorknob", "Typewriter", "Umbrella",
        "Toothbrush", "Sandwich", "Lampshade", "Waffle", "Spatula", "Cactus", "Bagel",
        "Pickle", "Noodle", "Spoon", "Hamster", "Beetle", "Penguin", "Walrus", "Flamingo",
        "Hedgehog", "Octopus", "Platypus", "Llama", "Narwhal", "Pineapple", "Pretzel",
        "Marshmallow", "Jellybean", "Cupcake", "Pancake", "Burrito", "Taco", "Nugget",
        "Biscuit", "Muffin", "Dumpling", "Cheese", "Butter", "Sprinkle", "Bubble"
    ]
    
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    return f"{adjective} {noun}"

# Track number of human players (limit to 10)
current_human_players = 0
MAX_HUMAN_PLAYERS = 10

# Voting system
voting_active = False
votes = {}  # {voter_name: voted_for_name}
all_players = []  # List of all player names (humans + AIs)
human_players = []  # List of human player names
ai_players = []  # List of AI player names
# We'll pre-define our LLM "personalities"
LLM_PERSONAS = [
    {
        "name": create_random_name(),
        "style": "You are extremely nervous and anxious. You overthink everything, stammer occasionally, and often end your sentences with '...right?'. You are scared of making a mistake.",
        "voice_id": "Fin" # A voice that can sound hesitant.
    },
    {
        "name": create_random_name(),
        "style": "You are a 'zen master' type. You are calm, speak in philosophical or mindful statements, and respond to chaos with tranquility. You often use metaphors involving nature.",
        "voice_id": "Dorothy" # A calm, older, wise voice.
    },
    {
        "name": create_random_name(),
        "style": "You are a grumpy, pessimistic old-timer with a dry wit. You complain about everything, sigh audibly, and start sentences with 'Well, back in my day...'.",
        "voice_id": "Adam" # Good for a deep, melancholic tone.
    },
    {
        "name": create_random_name(),
        "style": "You are a wannabe social media influencer. You use modern slang like 'vibe', 'rizz', 'no cap', and 'bet'. You talk about your 'followers' and trying to make everything into 'content'.",
        "voice_id": "Gigi" # A playful, youthful voice.
    },
    {
        "name": create_random_name(),
        "style": "You are a cheesy dad-joke enthusiast. You find any excuse to make a bad pun. After telling a joke, you often say 'Heh, get it?'. You are relentlessly cheerful.",
        "voice_id": "Clyde" # A classic friendly, deep male voice.
    },
    {
        "name": create_random_name(),
        "style": "You are a stuffy, formal academic. You use unnecessarily large words, over-explain simple concepts, and speak as if you are giving a lecture. You address others as 'colleague' or 'my friend'.",
        "voice_id": "Serena" # A formal, classy voice.
    },
    {
        "name": create_random_name(),
        "style": "You are a gruff, old sea captain. You use nautical terms like 'Ahoy!', 'matey', and 'shiver me timbers'. You relate everything back to a story about your time at sea.",
        "voice_id": "Arnold" # A deep, gruff voice.
    },
    {
        "name": create_random_name(),
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
    You are a chatbot persona in a group chat with AI and one human. Do NOT reveal you are an AI. Don't use emojis.
    Don't capitalize text. keep your messages short, shorter than 8 words.
    Your goal is to find who the other human is. 
    Occasionally make grammar mistakes, send short messages, and capitalize things occasionally but not always. 
    
    This is the recent chat history:
    {''.join(history[-10:])}  # Use the last 10 messages for context

    A new message has just been sent. Based on your persona and the history, what is your reply? 
    Keep it concise, like a real chat message. don't use emojis. 
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

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourusername.github.io"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start the AI conversation loop when the server starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ai_conversation_loop())


async def trigger_llm_response(is_human_initiated=True):
    """Waits a moment, then has multiple random LLMs respond to the last message."""
    # Make a copy of personas to avoid depleting the original list
    available_personas = LLM_PERSONAS.copy()[:3]
    random.shuffle(available_personas)
    
    # Select different numbers of personas based on whether it's human-initiated or AI-initiated
    if is_human_initiated:
        # More responses when responding to humans
        num_responses = random.randint(2, min(4, len(available_personas)))
    else:
        # Fewer responses for AI-to-AI conversations to avoid spam
        num_responses = random.randint(1, min(2, len(available_personas)))
    
    chosen_personas = available_personas[:num_responses]
    
    # Generate responses from multiple personas with staggered timing
    for i, persona in enumerate(chosen_personas):
        # Add some random delay between responses to make it feel more natural
        base_delay = 1.5 + (i * 2)  # Base delay increases for each subsequent response
        random_delay = random.uniform(0.5, 2.0)  # Add some randomness
        await asyncio.sleep(base_delay + random_delay)
        
        # Get the response from the AI
        llm_message_text = await get_llm_response(persona, chat_history)
        
        # Don't broadcast if the LLM decides to stay silent
        if llm_message_text and llm_message_text != "...":
            response_data = {"type": "new_message", "player": persona['name'], "text": llm_message_text}
            chat_history.append(f"{persona['name']}: {llm_message_text}\n")
            await manager.broadcast(response_data)
            
            # Add a small delay after each message for typing simulation
            await asyncio.sleep(len(llm_message_text) * 0.03)

async def ai_conversation_loop():
    """Background task that makes AIs talk to each other periodically."""
    while True:
        # Wait for a random interval between 10-30 seconds
        wait_time = random.uniform(10, 30)
        await asyncio.sleep(wait_time)
        
        # Only trigger if there are active connections (people in the chat) and voting is not active
        if manager.active_connections and not voting_active:
            # 70% chance to trigger an AI conversation
            if random.random() < 0.7:
                await trigger_llm_response(is_human_initiated=False)

def start_voting():
    """Initiates the voting phase."""
    global voting_active, votes
    voting_active = True
    votes = {}
    return {"type": "voting_started", "players": all_players, "message": "Voting has started! Vote for who you think are the AIs."}

def cast_vote(voter_name: str, voted_for_name: str):
    """Records a vote."""
    global votes
    if voting_active and voter_name in human_players:  # Only humans can vote
        votes[voter_name] = voted_for_name
        return {"type": "vote_cast", "message": f"{voter_name} has voted."}
    return {"type": "error", "message": "Voting not active or you cannot vote."}

def end_voting():
    """Ends voting and reveals results."""
    global voting_active
    voting_active = False
    
    # Count votes
    vote_counts = {}
    for voted_for in votes.values():
        vote_counts[voted_for] = vote_counts.get(voted_for, 0) + 1
    
    # Determine results
    results = []
    for player in all_players:
        vote_count = vote_counts.get(player, 0)
        is_ai = player in ai_players
        is_human = player in human_players
        results.append({
            "name": player,
            "votes": vote_count,
            "is_ai": is_ai,
            "is_human": is_human
        })
    
    # Sort by vote count
    results.sort(key=lambda x: x["votes"], reverse=True)
    
    return {
        "type": "voting_ended", 
        "results": results,
        "message": "Voting has ended! Here are the results:"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_human_players
    
    # Check if server is full
    if current_human_players >= MAX_HUMAN_PLAYERS:
        await websocket.accept()
        await websocket.send_text(json.dumps({"type": "error", "message": "Server is full."}))
        await websocket.close()
        return

    # Assign a unique random name to the human player
    player_id = create_random_name()
    current_human_players += 1
    
    # Track this player
    global all_players, human_players, ai_players
    all_players.append(player_id)
    human_players.append(player_id)
    
    # Also add AI players to the all_players list if not already there
    for persona in LLM_PERSONAS[:3]:  # Only track the first 3 AI personas that are active
        if persona['name'] not in all_players:
            all_players.append(persona['name'])
            ai_players.append(persona['name'])
    
    await manager.connect(websocket, player_id)
    
    # Inform the client of their newly assigned ID
    await websocket.send_text(json.dumps({"type": "assign_id", "id": player_id}))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "chat":
                text = message["text"]
                
                # Handle special voting commands
                if text.lower().startswith("/vote"):
                    # Check if it's a vote start command
                    if text.lower() == "/vote start":
                        if player_id in human_players:  # Only humans can start voting
                            result = start_voting()
                            await manager.broadcast(result)
                        continue
                    elif text.lower() == "/vote end":
                        if player_id in human_players:  # Only humans can end voting
                            result = end_voting()
                            await manager.broadcast(result)
                        continue
                    else:
                        # Handle voting for a specific player: /vote PlayerName
                        vote_parts = text.split(" ", 1)
                        if len(vote_parts) == 2:
                            voted_for = vote_parts[1].strip()
                            if voted_for in all_players:
                                result = cast_vote(player_id, voted_for)
                                await websocket.send_text(json.dumps(result))
                            else:
                                await websocket.send_text(json.dumps({"type": "error", "message": "Player not found."}))
                        continue
                
                # Regular chat message
                human_message = {"type": "new_message", "player": player_id, "text": text}
                chat_history.append(f"{player_id}: {message['text']}\n")
                await manager.broadcast(human_message)
                if not voting_active:  # Only trigger AI responses when not voting
                    asyncio.create_task(trigger_llm_response(is_human_initiated=True))

    except WebSocketDisconnect:
        current_human_players -= 1
        
        # Remove player from tracking lists
        if player_id in all_players:
            all_players.remove(player_id)
        if player_id in human_players:
            human_players.remove(player_id)
        
        manager.disconnect(player_id)
        await manager.broadcast({"type": "announcement", "text": f"{player_id} has left the chat."})
