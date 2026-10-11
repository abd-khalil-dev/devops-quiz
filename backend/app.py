import os
import socket
from flask import Flask, jsonify, request

app = Flask(__name__)

QUESTIONS = [
    {
        "id": 1,
        "question": "Docker image se chalne wali running instance ko kya kehte hain?",
        "options": ["Container", "Volume", "Registry", "Dockerfile"],
        "answer": 0,
    },
    {
        "id": 2,
        "question": "Kubernetes mein pods ko desired count par rakhne wala object?",
        "options": ["Service", "Deployment", "ConfigMap", "Namespace"],
        "answer": 1,
    },
    {
        "id": 3,
        "question": "Helm mein installed chart ke instance ko kya kehte hain?",
        "options": ["Release", "Repo", "Template", "Revision"],
        "answer": 0,
    },
]


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/info")
def info():
    # Footer ke liye: kaunsa pod aur kaunsa version
    return jsonify(
        pod=os.getenv("HOSTNAME", socket.gethostname()),
        version=os.getenv("APP_VERSION", "dev"),
    )


@app.get("/api/questions")
def questions():
    # Sahi jawab client ko nahi bhejte
    return jsonify([{k: v for k, v in q.items() if k != "answer"} for q in QUESTIONS])


@app.post("/api/submit")
def submit():
    data = request.get_json(silent=True) or {}
    answers = data.get("answers", {})
    score = sum(1 for q in QUESTIONS if answers.get(str(q["id"])) == q["answer"])
    return jsonify(score=score, total=len(QUESTIONS))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
