import logging
import os
import tempfile
import json
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from app.config.config import settings
from app.service.llm.llm import LLMService
from app.service.hebert.hebert import HeBERTService
from app.service.stt.stt import STTService
from app.service.tts.tts import TTSService
from app.service.stanza.stanza import StanzaService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SoftSkill AI Service")

# Initialize Services
llm_service = LLMService(model=settings.LLM_MODEL)
hebert_service = HeBERTService(model_name=settings.HEBERT_MODEL_NAME)
stt_service = STTService()
tts_service = TTSService(lang=settings.STANZA_LANG)
stanza_service = StanzaService(lang=settings.STANZA_LANG)

# --- Pydantic Models ---
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str
    sentiment: Optional[str] = None

class ReportRequest(BaseModel):
    sessionId: int
    messages: List[Message]

# --- Routes ---

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/ai/tts")
async def text_to_speech(req: TTSRequest):
    try:
        audio_base64 = tts_service.text_to_speech_base64(req.text)
        return {"audioContent": audio_base64}
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/interact")
async def interact(
    audio: UploadFile = File(None),
    text: Optional[str] = Form(None),
    session_id: str = Form(...),
    scenario_prompt: str = Form(""),
    chat_history: str = Form("[]") # JSON string of messages
):
    """
    Handles the interaction: STT -> Sentiment -> LLM (Streaming) -> TTS
    """
    
    # 1. Get User Input (either from audio or text)
    user_input = text or ""
    if audio:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        try:
            user_input = stt_service.transcribe(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    if not user_input:
        raise HTTPException(status_code=400, detail="No input provided (audio or text)")

    logger.info(f"User Input: {user_input}")

    # 2. Analyze Sentiment (HeBERT)
    sentiment_result = hebert_service.analyze_sentiment(user_input)
    logger.info(f"Sentiment: {sentiment_result}")

    # 3. Analyze NLP (Stanza)
    nlp_analysis = stanza_service.analyze_text(user_input)

    # 4. Construct Messages for LLM
    # The Sandwich Prompt: System Rules + Persona + Dynamic Sentiment/Safety + History + User Input
    messages = [
        {"role": "system", "content": f"You are an AI trainer for social skills. {scenario_prompt}"},
        {"role": "system", "content": f"Current user sentiment: {sentiment_result['label']}. Adjust your tone accordingly."}
    ]
    
    try:
        history = json.loads(chat_history)
        # Ensure history is in the format expected by LLM (role, content)
        for msg in history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    except:
        pass
        
    messages.append({"role": "user", "content": user_input})

    # 5. Stream LLM Response
    async def response_generator():
        # First yield the recognized text and sentiment for the frontend to update UI
        yield f"data: {json.dumps({'type': 'user_input', 'text': user_input, 'sentiment': sentiment_result})}\\n\n"
        
        full_response = ""
        async for token in llm_service.stream_response(messages):
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\\n\n"
        
        # Finally, send a completion event with any extra data
        yield f"data: {json.dumps({'type': 'done', 'analysis': nlp_analysis})}\\n\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")

@app.post("/ai/report/generate")
async def generate_report(req: ReportRequest):
    """
    Generates a detailed behavioral report based on the provided session history.
    This analysis is stateless and relies on the data sent by the backend.
    """
    logger.info(f"Generating report for session {req.sessionId} with {len(req.messages)} messages")

    if not req.messages:
        return {
            "sessionId": req.sessionId,
            "summary": "No messages to analyze.",
            "metrics": {"average_sentiment": "neutral", "social_impact_score": 0},
            "strengths": [],
            "tips": []
        }

    # 1. Calculate Quantitative Metrics
    user_msgs = [m for m in req.messages if m.role == 'user']
    if not user_msgs:
         return {
            "sessionId": req.sessionId,
            "summary": "The session contained no user messages.",
            "metrics": {"average_sentiment": "neutral", "social_impact_score": 0}
        }

    # Calculate sentiment score (-1 to 1)
    sentiment_score_map = {"positive": 1, "neutral": 0, "negative": -1}
    total_sentiment = 0
    valid_sentiments = 0
    
    for m in user_msgs:
        if m.sentiment and m.sentiment.lower() in sentiment_score_map:
            total_sentiment += sentiment_score_map[m.sentiment.lower()]
            valid_sentiments += 1
    
    avg_sentiment_val = total_sentiment / valid_sentiments if valid_sentiments > 0 else 0
    
    # Map back to string
    avg_sentiment_str = "neutral"
    if avg_sentiment_val > 0.3: avg_sentiment_str = "positive"
    elif avg_sentiment_val < -0.3: avg_sentiment_str = "negative"

    # 2. Qualitative Analysis via LLM
    # Format history for the LLM
    conversation_text = ""
    for m in req.messages:
        conversation_text += f"{m.role.upper()}: {m.content}\n"

    prompt = f"""
    Analyze the following conversation from a social skills training session.
    The user is practicing social interactions.
    
    Conversation:
    {conversation_text}
    
    Task:
    1. Write a brief professional summary of the user's performance (in Hebrew).
    2. List 2 key strengths (in Hebrew).
    3. List 2 tips for improvement (in Hebrew).
    4. Give a score from 0 to 100 based on social appropriateness.
    
    Output strictly in valid JSON format like this:
    {{
        "summary": "...",
        "strengths": ["...", "..."],
        "tips": ["...", "..."],
        "score": 85
    }}
    """

    try:
        # Generate full response (not streaming)
        llm_response = await llm_service.generate_response([{"role": "user", "content": prompt}], format="json")
        
        # Parse JSON
        # Note: some LLMs might add markdown backticks, strip them
        clean_json = llm_response.replace("```json", "").replace("```", "").strip()
        analysis_data = json.loads(clean_json)
        
        summary = analysis_data.get("summary", "Analysis completed.")
        strengths = analysis_data.get("strengths", [])
        tips = analysis_data.get("tips", [])
        score = analysis_data.get("score", 0)

    except Exception as e:
        logger.error(f"LLM Analysis Failed: {e}")
        # Fallback if LLM fails or produces invalid JSON
        summary = "Could not generate detailed AI analysis at this time."
        strengths = ["Participation"]
        tips = ["Continue practicing"]
        score = 50 + (avg_sentiment_val * 20) # Rough fallback score based on sentiment

    # 3. Return Final Report
    return {
        "sessionId": req.sessionId,
        "summary": summary,
        "metrics": {
            "average_sentiment": avg_sentiment_str,
            "social_impact_score": score
        },
        "strengths": strengths,
        "tips": tips
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)