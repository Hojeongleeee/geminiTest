from flask import Flask, request, jsonify
import google.generativeai as genai
import uuid
import secrets
import os  # 환경변수 불러오는 용도
from flask_cors import CORS  # GitHub Pages에서 프론트 호출 허용

# Gemini API 설정
# genai.configure(api_key="YOUR_API_KEY")  # 실제 API 키로 변경 필요
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))


app = Flask(__name__)
CORS(app)  # 모든 도메인에서 API 호출 허용 (보안 필요시 제한 가능)
app.secret_key = secrets.token_hex(24)

# Gemini 모델
model = genai.GenerativeModel("gemini-2.0-flash-001")
chat_sessions = {}

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")
    session_id = data.get("session_id")

    if not session_id or session_id not in chat_sessions:
        chat = model.start_chat()
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = chat
        history = []
    else:
        chat = chat_sessions[session_id]
        history = data.get("history", [])

    response = chat.send_message(question)
    answer = response.text

    # 새 대화 내역
    history.append({"type": "question", "content": question})
    history.append({"type": "answer", "content": answer})

    return jsonify({
        "session_id": session_id,
        "history": history
    })

@app.route("/")
def home():
    return "Gemini API 서버가 작동 중입니다."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render가 지정한 포트를 우선 사용
    app.run(host="0.0.0.0", port=port)
    # app.run(debug=True)
