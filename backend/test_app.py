from app import app, QUESTIONS

client = app.test_client()


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_question_bank_is_valid():
    assert len(QUESTIONS) >= 50
    for q in QUESTIONS:
        assert len(q["options"]) == 4
        assert len(set(q["options"])) == 4
        assert 0 <= q["answer"] < 4
        assert q["explanation"]


def test_questions_hide_answers():
    data = client.get("/api/questions?count=5").get_json()
    assert len(data) == 5
    for q in data:
        assert "answer" not in q and "explanation" not in q


def test_category_filter():
    data = client.get("/api/questions?category=Helm&count=10").get_json()
    assert {q["category"] for q in data} == {"Helm"}


def test_answer_checks_the_text():
    q = QUESTIONS[0]
    right = q["options"][q["answer"]]
    ok = client.post("/api/answer", json={"id": q["id"], "choice": right}).get_json()
    assert ok["correct"] is True
    wrong = next(o for o in q["options"] if o != right)
    bad = client.post("/api/answer", json={"id": q["id"], "choice": wrong}).get_json()
    assert bad["correct"] is False
    assert bad["answer"] == right


def test_unknown_question_returns_404():
    r = client.post("/api/answer", json={"id": 9999, "choice": "x"})
    assert r.status_code == 404
