from app.config import AppConfig
from app.models import Page
from app.relevance_classifier import score_relevance


def test_relevance_scores_stem_and_teacher_training():
    config = AppConfig(relevance_keywords={"stem": 30, "teacher training": 20})
    score, evidence = score_relevance([Page("https://x.org", "", "STEM teacher training", "")], config)
    assert score == 50
    assert "stem" in evidence.lower()
