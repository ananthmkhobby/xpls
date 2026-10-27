from app.models import Person
from app.person_ranker import rank_people


def test_founder_beats_program_manager():
    key, alt = rank_people([
        Person(name="Asha Rao", designation="Program Manager", relevance_score=85),
        Person(name="Meera Singh", designation="Founder", relevance_score=100),
    ])
    assert key.name == "Meera Singh"
    assert alt.name == "Asha Rao"
