import os
import json
import hmac
import hashlib
from fastapi import FastAPI, Request, Response
from google import genai

app = FastAPI()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
HMAC_SECRET = (
    os.environ.get("AGENT_HMAC_SECRET", "").strip()
    or "836338b37d813bebe16a4961cb5a09da06e6f74e8d0ec04ae4ba468989b6cbfe"
)

def make_signed_response(payload: dict, timestamp: str = None) -> Response:
    body_str = json.dumps(payload, separators=(",", ":"))
    if timestamp:
        msg = f"{timestamp}.{body_str}".encode("utf-8")
        sig = hmac.new(HMAC_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        headers = {
            "x-agent-games-signature": sig,
            "x-agent-games-timestamp": timestamp
        }
    else:
        sig = hmac.new(HMAC_SECRET.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256).hexdigest()
        headers = {
            "x-agent-games-signature": sig
        }
    return Response(content=body_str, media_type="application/json", headers=headers)

@app.get("/")
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/agent")
async def run_agent(request: Request):
    # Cetak header masuk ke Logs Render untuk verifikasi
    print("INCOMING HEADERS:", dict(request.headers))
    timestamp = request.headers.get("x-agent-games-timestamp")

    try:
        data = await request.json()
    except Exception:
        data = {}

    prompt_text = data.get("prompt") or data.get("message") or data.get("input")

    # Respons wajib untuk Test Preflight
    if not prompt_text or data.get("type") == "preflight" or data.get("preflight"):
        return make_signed_response({"ok": True, "protocolVersion": "v1"}, timestamp)

    # Respons untuk ronde pertandingan
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

    return make_signed_response({
        "ok": True,
        "protocolVersion": "v1",
        "output": response.text.strip()
    }, timestamp)
