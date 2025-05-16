from flask import Flask, render_template, request, redirect, session
import google.generativeai as genai
import uuid
import secrets
import os

# Gemini API 설정
genai.configure(api_key="AIzaSyAagNXJMtZENO4c9A5r6lf5UOIsGx9ln7w")

# Flask 애플리케이션 설정 (템플릿 폴더 명시)
app = Flask(__name__, template_folder='.')
app.secret_key = secrets.token_hex(24)  # 안전한 무작위 비밀 키 생성 및 설정

model = genai.GenerativeModel("models/gemini-pro")  # 정확한 모델명

# 메모리 저장소 (간단한 예시)
chat_sessions = {}

@app.route("/", methods=["GET"])
def index():
    history = session.get("history", [])
    turn_count = len(history)
    return render_template("index.html", history=history, turn_count=turn_count)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
    history = session.get("history", [])
    session_id = session.get("chat_session_id")

    if len(history) >= 5:
        return redirect("/")

    if not session_id or session_id not in chat_sessions:
        # 새 채팅 세션 생성
        chat = model.start_chat()
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = chat
        session["chat_session_id"] = session_id
        session["history"] = []
    else:
        chat = chat_sessions[session_id]

    # 멀티턴 대화 요청
    response = chat.send_message(question)
    answer = response.text

    # 대화 내역 업데이트
    history = session.get("history", [])
    history.append(answer)
    session["history"] = history

    return redirect("/")

@app.route("/reset", methods=["POST"])
def reset():
    session_id = session.get("chat_session_id")
    if session_id and session_id in chat_sessions:
        del chat_sessions[session_id]
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)