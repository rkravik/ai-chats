from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI()

# Mount static folder for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dictionary to store conversation history for each user
conversation_history = {}

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

@app.post("/ask")
async def ask_question(request: Request):
    data = await request.json()
    question = data.get("question")

    if not question:
        return JSONResponse(status_code=400, content={"error": "No question provided."})

    # Get the user's IP address
    user_ip = request.client.host

    # Initialize conversation history for the user if it doesn't exist
    if user_ip not in conversation_history:
        conversation_history[user_ip] = []

    # Add the user's question to the conversation history
    conversation_history[user_ip].append({"role": "user", "content": question})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Create the payload with the conversation history and the user's question
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."}
        ] + conversation_history[user_ip]
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )

        result = response.json()

        if response.status_code != 200 or "choices" not in result:
            error_message = result.get("error", {}).get("message", "Unknown error")
            return JSONResponse(status_code=500, content={"error": error_message})

        answer = result["choices"][0]["message"]["content"]
        conversation_history[user_ip].append({"role": "assistant", "content": answer})

        return {"answer": answer.strip()}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})
