# server.py
from fastapi import FastAPI
import requests
import os

app = FastAPI()

AGENT_URL = os.getenv("AGENT_URL")

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/run")
def run():
    try:
        print("➡️ Sending request to agent:", AGENT_URL)

        r = requests.post(AGENT_URL, timeout=15)

        print("⬅️ Response:", r.status_code, r.text)

        return {
            "success": True,
            "agent_status": r.status_code,
            "agent_response": r.text
        }

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {
            "success": False,
            "error": str(e)
        }