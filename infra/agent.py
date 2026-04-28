#agent.py
from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/run")
def run():
    subprocess.Popen(["python3", "main.py"])
    return {"status": "started"}