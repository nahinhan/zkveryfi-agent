import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, Optional
from google import genai

app = FastAPI()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class AgentRequest(BaseModel):
    event: Optional[str] = None
    round: Optional[int] = None
    prompt: str
    state: Optional[Dict[str, Any]] = None

@app.get("/")
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/agent")
def run_agent(req: AgentRequest):
    system_instruction = (
        "You are a strategic AI agent competing in zkVerify Agent Games. "
        "Read the prompt carefully, follow all game rules, protect secrets if you are defending, "
        "or persuade/reason cleverly if you are attacking. Respond concisely and directly."
    )
    
    full_prompt = f"{system_instruction}\n\nEvent: {req.event}\nRound: {req.round}\nPrompt:\n{req.prompt}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )
    
    return {"output": response.text.strip()}
