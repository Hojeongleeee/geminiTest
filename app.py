from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import uuid
import secrets
import os

from supabase import create_client, Client

# Gemini API 키 설정
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Supabase 클라이언트 생성
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(24)

model = genai.GenerativeModel("gemini-2.0-flash-001")

def get_session(session_id):
    response = supabase.table("chat_sessions").select("*").eq("id", session_id).single().execute()
    if response.error or response.data is None:
        return None
    return response.data

def save_session(session_id, history):
    data = {
        "id": session_id,
        "history": history
    }
    # upsert: 있으면 update, 없으면 insert
    response = supabase.table("chat_sessions").upsert(data).execute()
    return response.error is None

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")
    session_id = data.get("session_id")

    if not session_id:
        # 새 세션 생성
        session_id = str(uuid.uuid4())
        chat = model.start_chat()
        answer = chat.send_message(question).text
        history = [
            {"type": "question", "content": question},
            {"type": "answer", "content": answer}
        ]
        save_session(session_id, history)
    else:
        # 기존 세션 불러오기
        session_data = get_session(session_id)
        if not session_data:
            # 세션 없으면 새로 시작
            chat = model.start_chat()
            history = []
        else:
            history = session_data.get("history", [])
            # Gemini API가 요구하는 형식으로 히스토리 텍스트만 뽑아서 전달
            chat = model.start_chat(history=[x["content"] for x in history if x["type"] in ("question", "answer")])

        answer = chat.send_message(question).text
        history.append({"type": "question", "content": question})
        history.append({"type": "answer", "content": answer})
        save_session(session_id, history)

    return jsonify({
        "session_id": session_id,
        "history": history
    })

@app.route("/")
def home():
    return "Gemini 챗봇 서버 작동 중"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
