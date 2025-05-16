
#  AIzaSyAagNXJMtZENO4c9A5r6lf5UOIsGx9ln7w

from flask import Flask, render_template, request, redirect, session
import google.generativeai as genai
import uuid
import secrets
import os
from markdown import markdown  # 마크다운 라이브러리 import

# Gemini API 설정
genai.configure(api_key="AIzaSyAagNXJMtZENO4c9A5r6lf5UOIsGx9ln7w")  # 실제 API 키로 변경 필요

# Flask 애플리케이션 설정 (템플릿 폴더 명시)
app = Flask(__name__, template_folder='.')
app.secret_key = secrets.token_hex(24)  # 안전한 무작위 비밀 키 생성 및 설정

# Gemini Pro 모델 -> Gemini 2.0 Flash 001 모델로 변경
model = genai.GenerativeModel("gemini-2.0-flash-001")

# 메모리 저장소 (간단한 예시)
chat_sessions = {}

@app.route("/", methods=["GET", "POST"])
def index():
    history_with_question = session.get("history_with_question", [])
    turn_count = len(history_with_question) // 2  # 질문-답변 쌍이므로 2로 나눔
    return render_template("index.html", history_with_question=history_with_question, turn_count=turn_count)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.form["question"]
    history_with_question = session.get("history_with_question", [])
    session_id = session.get("chat_session_id")

    if len(history_with_question) >= 10:  # 질문-답변 쌍이므로 최대 5번 대화는 10개 항목
        return redirect("/")

    if not session_id or session_id not in chat_sessions:
        # 새 채팅 세션 생성
        chat = model.start_chat()
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = chat
        session["chat_session_id"] = session_id
        session["history_with_question"] = []
    else:
        chat = chat_sessions[session_id]

    # 멀티턴 대화 요청
    response = chat.send_message(question)
    answer = response.text

    # 대화 내역 업데이트 (질문과 답변 함께 저장)
    history_with_question = session.get("history_with_question", [])
    history_with_question.append({"type": "question", "content": question})
    history_with_question.append({"type": "answer", "content": answer})
    session["history_with_question"] = history_with_question

    return redirect("/")

@app.route("/reset", methods=["POST"])
def reset():
    session_id = session.get("chat_session_id")
    if session_id and session_id in chat_sessions:
        del chat_sessions[session_id]
    session.clear()
    return redirect("/")

# 템플릿에서 마크다운을 렌더링하는 필터 함수
app.jinja_env.filters['markdown'] = markdown

if __name__ == "__main__":
    app.run(debug=True)