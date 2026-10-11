import os
import socket
from flask import Flask, jsonify, request

app = Flask(__name__)

QUESTIONS = [
    {"id": 1, "category": "Docker",
     "question": "What is a container?",
     "options": ["A running copy of an image", "A file that lists dependencies",
                 "A website that stores images", "A tool to write code"],
     "answer": 0,
     "explanation": "An image is the blueprint. A container is the running copy of that blueprint."},
    {"id": 2, "category": "Docker",
     "question": "Which file tells Docker how to build an image?",
     "options": ["docker-compose.yml", "Dockerfile", "values.yaml", "app.py"],
     "answer": 1,
     "explanation": "The Dockerfile has the build steps. Compose is for running many containers together."},
    {"id": 3, "category": "Git",
     "question": "Which command saves your changes in the Git history?",
     "options": ["git push", "git add", "git commit", "git clone"],
     "answer": 2,
     "explanation": "git add picks the changes, git commit saves them, and git push sends them to GitHub."},
    {"id": 4, "category": "Git",
     "question": "What is a branch in Git?",
     "options": ["A copy of the repo on another server", "A separate line of work in the same repo",
                 "A backup file", "A type of commit message"],
     "answer": 1,
     "explanation": "A branch lets you work on a feature without touching the main code."},
    {"id": 5, "category": "CI/CD",
     "question": "What does CI do when you push code?",
     "options": ["Deletes the old code", "Builds and tests the code automatically",
                 "Buys a new server", "Writes the documentation"],
     "answer": 1,
     "explanation": "CI means Continuous Integration. It checks every push, so bugs show up early."},
    {"id": 6, "category": "Kubernetes",
     "question": "Which object keeps the right number of pods running?",
     "options": ["Service", "Namespace", "Deployment", "ConfigMap"],
     "answer": 2,
     "explanation": "A Deployment keeps the replica count. If a pod dies, it creates a new one."},
    {"id": 7, "category": "Kubernetes",
     "question": "Why do we use a Service?",
     "options": ["To store data on disk", "To give pods one stable address",
                 "To build images", "To add more nodes"],
     "answer": 1,
     "explanation": "Pod IPs change all the time. A Service gives them one fixed name and address."},
    {"id": 8, "category": "Kubernetes",
     "question": "Which object is best for a database that needs a fixed name and its own disk?",
     "options": ["Deployment", "StatefulSet", "DaemonSet", "Job"],
     "answer": 1,
     "explanation": "A StatefulSet gives pods fixed names like db-0 and a separate disk for each pod."},
    {"id": 9, "category": "Helm",
     "question": "What is a Helm release?",
     "options": ["A new version of Kubernetes", "An installed copy of a chart in your cluster",
                 "A Docker image tag", "A GitHub tag"],
     "answer": 1,
     "explanation": "The chart is the package. The release is that package running in your cluster."},
    {"id": 10, "category": "Cloud",
     "question": "What does Terraform do?",
     "options": ["Creates cloud resources from code", "Runs containers",
                 "Tests Python code", "Watches CPU usage"],
     "answer": 0,
     "explanation": "Terraform is Infrastructure as Code. You describe servers and networks in files, and it builds them."},
]


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/info")
def info():
    return jsonify(
        pod=os.getenv("HOSTNAME", socket.gethostname()),
        version=os.getenv("APP_VERSION", "dev"),
    )


@app.get("/api/questions")
def questions():
    hidden = ("answer", "explanation")
    return jsonify([{k: v for k, v in q.items() if k not in hidden} for q in QUESTIONS])


@app.post("/api/answer")
def answer():
    data = request.get_json(silent=True) or {}
    q = next((q for q in QUESTIONS if q["id"] == data.get("id")), None)
    if q is None:
        return jsonify(error="unknown question"), 404
    return jsonify(
        correct=(data.get("choice") == q["answer"]),
        answer=q["answer"],
        explanation=q["explanation"],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
