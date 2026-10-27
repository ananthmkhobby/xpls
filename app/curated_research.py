from __future__ import annotations

from app.program_extractor import ProgramResearch


CURATED_PROGRAM_RESEARCH = {
    "akshaya patra": ProgramResearch(
        named_programme="Beyond Meals; School Rejuvenation Programme; Giving Every Dream a Chance",
        what_they_do=(
            "Akshaya Patra reaches government-school children at scale and runs Beyond Meals initiatives, "
            "including the School Rejuvenation Programme and Giving Every Dream a Chance, which connect "
            "nutrition with the wider school learning environment."
        ),
        custom_appreciation=(
            "We were glad to see your Beyond Meals initiatives, particularly the School Rejuvenation Programme "
            "and Giving Every Dream a Chance, which treat a child's learning environment as part of the mission "
            "alongside nutrition."
        ),
        why_xperimentor_fits=(
            "Given the reach of your school network and the infrastructure and academic interventions already "
            "under the School Rejuvenation Programme, we see potential to add hands-on science and math learning "
            "to the schools you already serve."
        ),
    )
}


def curated_program_research(organisation_name: str = "", website: str = "") -> ProgramResearch:
    key_source = f"{organisation_name} {website}".lower()
    for key, research in CURATED_PROGRAM_RESEARCH.items():
        if key in key_source:
            return research
    return ProgramResearch()
