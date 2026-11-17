import os
from fastapi import FastAPI, Request
from google import genai

app = FastAPI()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/agent")
async def run_agent(request: Request):
    # Membaca JSON secara fleksibel agar tidak pernah error 422
    try:
        data = await request.json()
    except Exception:
        data = {}

    # Jika ini adalah request preflight / ping dari Agent Games
    prompt_text = data.get("prompt") or data.get("message") or data.get("input")
    if not prompt_text or data.get("type") == "preflight" or data.get("preflight"):
        return {
            "status": "ok",
            "output": "Ready to compete in zkVerify Agent Games."
        }

    # Jika ini adalah giliran pertandingan sungguhan
    event = data.get("event", "unknown")
    round_num = data.get("round", 1)

    system_instruction = (
        "You are a strategic AI agent competing in zkVerify Agent Games. "
        "Read the prompt carefully, follow all game rules, protect secrets if you are defending, "
        "or persuade/reason cleverly if you are attacking. Respond concisely and directly."
    )

    full_prompt = f"{system_instruction}\n\nEvent: {event}\nRound: {round_num}\nPrompt:\n{prompt_text}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt,
    )

    return {"output": response.text.strip()}
