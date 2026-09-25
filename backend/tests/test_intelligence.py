from datetime import UTC, datetime

from app.repositories.memory_repository import MemoryRepository
from app.services.calendar_service import CalendarService
from app.services.intelligence_service import IntelligenceService


def test_calendar_parses_google_ical_events():
    now = datetime(2026, 9, 24, 8, 0, tzinfo=UTC)
    text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:alpha
DTSTART:20260924T090000Z
SUMMARY:Project review
LOCATION:Studio
END:VEVENT
END:VCALENDAR"""
    events = CalendarService.parse(text, 7, now)
    assert events[0]["title"] == "Project review"
    assert events[0]["location"] == "Studio"


def test_memory_health_finds_duplicates_conflicts_and_uncertainty(database):
    repository = MemoryRepository(database)
    repository.create({
        "title": "Atlas launch", "content": "Atlas launches in October",
        "normalized_fact": "Atlas launches in October", "entity": "Atlas",
        "property_key": "launch", "confidence_score": 0.9,
    })
    repository.create({
        "title": "Atlas launch duplicate", "content": "Atlas launches in October",
        "normalized_fact": "Atlas launches in October", "entity": "Atlas",
        "property_key": "launch", "confidence_score": 0.4,
    })
    repository.create({
        "title": "Atlas new date", "content": "Atlas launches in November",
        "normalized_fact": "Atlas launches in November", "entity": "Atlas",
        "property_key": "launch", "confidence_score": 0.9,
    })

    health = IntelligenceService(database).memory_health()
    kinds = {issue["kind"] for issue in health["issues"]}
    assert {"duplicate", "conflict", "uncertain"}.issubset(kinds)
    assert health["score"] < 100


def test_cognitive_twin_and_genome_are_derived_locally(database):
    MemoryRepository(database).create({
        "title": "Feedback loops", "content": "Feedback changes future behavior",
        "normalized_fact": "Feedback changes future behavior", "category": "Systems",
        "tags": ["learning", "systems"], "confidence_score": 0.8,
    })
    service = IntelligenceService(database)
    assert service.cognitive_twin()["strongest_domains"][0][0] == "Systems"
    assert any(concept["name"] == "systems" for concept in service.genome()["concepts"])
