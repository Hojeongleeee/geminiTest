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

def save_session(session_id, history):
    data = {
        "id": session_id,
        "history": history
    }

    response = supabase.table("chat_sessions").upsert(data).execute()

    if response.data is not None:
        print("세션 저장 성공:", response.data)
        return True
    else:
        print("세션 저장 실패:", response)
        return False



def get_session(session_id):
    response = supabase.table("chat_sessions").select("*").eq("id", session_id).execute()

    if response.data and len(response.data) > 0:
        print("세션 불러오기 성공:", response.data)
        return response.data[0]  # 첫 번째 결과만 반환
    else:
        print("세션 없음 또는 실패:", response)
        return None


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")
    session_id = data.get("session_id")
    print("세션 ID:", session_id)  # Render 로그에서 확인 가능

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
            chat = model.start_chat()
            history = []
        else:
            history = session_data.get("history", [])
            # 🔧 수정된 부분: Gemini 형식으로 변환
            chat_history = [
                {"role": "user", "parts": [x["content"]]} if x["type"] == "question" else
                {"role": "model", "parts": [x["content"]]}
                for x in history if x["type"] in ("question", "answer")
            ]
            chat = model.start_chat(history=chat_history)

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
