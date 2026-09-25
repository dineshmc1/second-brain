from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.database import Database, db
from app.services.calendar_service import CalendarService


def _tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2}


class IntelligenceService:
    def __init__(self, database: Database = db) -> None:
        self.db = database

    def overview(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        week_start = now - timedelta(days=7)
        with self.db.connect() as connection:
            inbox = connection.execute("SELECT COUNT(*) FROM inbox_items WHERE status='unprocessed'").fetchone()[0]
            tasks = [dict(row) for row in connection.execute(
                """SELECT t.*,p.name project_name,p.color project_color FROM tasks t
                   LEFT JOIN projects p ON p.id=t.project_id
                   WHERE t.status NOT IN ('done','completed')
                   ORDER BY CASE t.priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
                            t.due_at IS NULL,t.due_at,t.position LIMIT 12"""
            ).fetchall()]
            completed = connection.execute(
                "SELECT COUNT(*) FROM tasks WHERE status IN ('done','completed') AND COALESCE(completed_at,updated_at)>=?",
                (week_start.isoformat(),),
            ).fetchone()[0]
            created = connection.execute(
                "SELECT COUNT(*) FROM tasks WHERE created_at>=?", (week_start.isoformat(),)
            ).fetchone()[0]
            memories = connection.execute("SELECT COUNT(*) FROM memories WHERE status='current'").fetchone()[0]
            mastered = connection.execute("SELECT COUNT(*) FROM learning_nodes WHERE status='mastered'").fetchone()[0]
            total_nodes = connection.execute("SELECT COUNT(*) FROM learning_nodes").fetchone()[0]
            active_projects = connection.execute("SELECT COUNT(*) FROM projects WHERE status='active'").fetchone()[0]
        calendar_error = None
        try:
            events = CalendarService().upcoming(7)
        except Exception as exc:
            events, calendar_error = [], str(exc)
        denominator = max(completed + len(tasks), 1)
        weekly_progress = round(completed / denominator * 100)
        return {
            "generated_at": now.isoformat(),
            "inbox_count": inbox,
            "today_tasks": tasks[:6],
            "calendar_events": events,
            "calendar_error": calendar_error,
            "weekly": {
                "completed": completed, "created": created,
                "remaining": len(tasks), "progress": weekly_progress,
            },
            "metrics": {
                "current_memories": memories, "active_projects": active_projects,
                "mastered_nodes": mastered, "total_nodes": total_nodes,
            },
        }

    def memory_health(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        with self.db.connect() as connection:
            rows = [dict(row) for row in connection.execute(
                "SELECT id,title,normalized_fact,entity,property_key,status,confidence_score,effective_until,updated_at FROM memories WHERE status!='deleted' ORDER BY updated_at DESC LIMIT 500"
            ).fetchall()]
        issues: list[dict[str, Any]] = []
        seen_pairs: set[tuple[str, str]] = set()
        token_sets = {row["id"]: _tokens(row["normalized_fact"]) for row in rows}
        for index, left in enumerate(rows):
            for right in rows[index + 1:]:
                a, b = token_sets[left["id"]], token_sets[right["id"]]
                if not a or not b:
                    continue
                similarity = len(a & b) / max(len(a | b), 1)
                if similarity >= 0.82:
                    key = tuple(sorted((left["id"], right["id"])))
                    if key not in seen_pairs:
                        issues.append(self._issue("duplicate", "Possible duplicate", left, right, similarity))
                        seen_pairs.add(key)
            if left["status"] == "uncertain" or float(left["confidence_score"]) < 0.6:
                issues.append(self._issue("uncertain", "Low-confidence memory", left))
            if left["effective_until"] and self._as_datetime(left["effective_until"]) < now:
                issues.append(self._issue("outdated", "Validity date has passed", left))
            elif self._as_datetime(left["updated_at"]) < now - timedelta(days=365):
                issues.append(self._issue("outdated", "Not reviewed for over a year", left))

        grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in rows:
            if row["entity"] and row["property_key"] and row["status"] == "current":
                grouped[(row["entity"].lower(), row["property_key"])].append(row)
        for group in grouped.values():
            facts = {item["normalized_fact"].strip().lower() for item in group}
            if len(group) > 1 and len(facts) > 1:
                issues.append(self._issue("conflict", "Conflicting current facts", group[0], group[1]))
        counts = Counter(issue["kind"] for issue in issues)
        score = max(0, 100 - counts["conflict"] * 12 - counts["duplicate"] * 5 - counts["outdated"] * 2 - counts["uncertain"] * 4)
        return {"score": score, "counts": dict(counts), "issues": issues[:100], "scanned": len(rows)}

    def cognitive_twin(self) -> dict[str, Any]:
        with self.db.connect() as connection:
            memories = [dict(row) for row in connection.execute(
                "SELECT memory_type,category,tags_json,confidence_score,importance_score FROM memories WHERE status='current'"
            ).fetchall()]
            attempts = [dict(row) for row in connection.execute(
                "SELECT mode,score,misconceptions_json FROM learning_attempts ORDER BY created_at DESC LIMIT 100"
            ).fetchall()]
            settings = {row["key"]: json.loads(row["value_json"]) for row in connection.execute("SELECT * FROM settings")}
        types = Counter(item["memory_type"] for item in memories)
        categories = Counter(item["category"] or "Uncategorized" for item in memories)
        modes = Counter(item["mode"] for item in attempts)
        misconceptions: Counter[str] = Counter()
        for attempt in attempts:
            misconceptions.update(json.loads(attempt["misconceptions_json"] or "[]"))
        avg_confidence = round(sum(float(item["confidence_score"]) for item in memories) / max(len(memories), 1) * 100)
        return {
            "knowledge_count": len(memories),
            "confidence": avg_confidence,
            "dominant_memory_types": types.most_common(5),
            "strongest_domains": categories.most_common(6),
            "learning_modes_used": modes.most_common(),
            "recurring_misconceptions": misconceptions.most_common(6),
            "preferences": {
                "explanation_style": settings.get("explanation_style", "adaptive"),
                "challenge_level": settings.get("challenge_level", "balanced"),
                "session_minutes": settings.get("session_minutes", 25),
            },
            "insight": self._twin_insight(memories, attempts, categories),
        }

    def genome(self) -> dict[str, Any]:
        with self.db.connect() as connection:
            memories = [dict(row) for row in connection.execute(
                "SELECT category,tags_json,confidence_score,importance_score FROM memories WHERE status='current'"
            ).fetchall()]
            nodes = [dict(row) for row in connection.execute(
                "SELECT id,goal_id,title,status,mastery,sequence,prerequisites_json FROM learning_nodes ORDER BY goal_id,sequence"
            ).fetchall()]
            goals = [dict(row) for row in connection.execute("SELECT * FROM learning_goals ORDER BY updated_at DESC").fetchall()]
        concepts: Counter[str] = Counter()
        confidence: defaultdict[str, list[float]] = defaultdict(list)
        for item in memories:
            labels = [item["category"]] if item["category"] else []
            labels += json.loads(item["tags_json"] or "[]")
            for label in set(filter(None, labels)):
                concepts[label] += 1
                confidence[label].append(float(item["confidence_score"]))
        concept_rows = [{
            "name": name, "evidence": count,
            "confidence": round(sum(confidence[name]) / len(confidence[name]) * 100),
        } for name, count in concepts.most_common(40)]
        return {"concepts": concept_rows, "goals": goals, "nodes": nodes}

    def resurface(self, project_id: str) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        with self.db.connect() as connection:
            rows = [dict(row) for row in connection.execute(
                """SELECT id,title,normalized_fact,memory_type,importance_score,confidence_score,updated_at
                   FROM memories WHERE project_id=? AND status='current' ORDER BY updated_at ASC LIMIT 100""",
                (project_id,),
            ).fetchall()]
        surfaced = []
        for row in rows:
            age = max((now - self._as_datetime(row["updated_at"])).days, 0)
            score = float(row["importance_score"]) * 0.55 + min(age / 180, 1) * 0.3 + (1 - float(row["confidence_score"])) * 0.15
            reason = "Important project knowledge"
            if float(row["confidence_score"]) < 0.65:
                reason = "Needs confirmation"
            elif age > 60:
                reason = f"Not revisited for {age} days"
            surfaced.append({**row, "resurface_score": round(score, 3), "reason": reason})
        return sorted(surfaced, key=lambda item: item["resurface_score"], reverse=True)[:6]

    @staticmethod
    def _issue(kind: str, reason: str, memory: dict, related: dict | None = None, similarity: float | None = None) -> dict:
        return {
            "kind": kind, "reason": reason,
            "memory": {"id": memory["id"], "title": memory["title"], "fact": memory["normalized_fact"]},
            "related": ({"id": related["id"], "title": related["title"], "fact": related["normalized_fact"]} if related else None),
            "similarity": round(similarity, 2) if similarity is not None else None,
        }

    @staticmethod
    def _as_datetime(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    @staticmethod
    def _twin_insight(memories: list[dict], attempts: list[dict], categories: Counter) -> str:
        if not memories:
            return "Capture a few durable memories and complete a learning session so your cognitive twin can identify patterns."
        strongest = categories.most_common(1)[0][0]
        if not attempts:
            return f"Your knowledge is strongest around {strongest}. A diagnostic learning session will reveal comprehension gaps."
        scored = [float(item["score"]) for item in attempts if item["score"] is not None]
        if scored and sum(scored) / len(scored) < 65:
            return f"You retain useful context in {strongest}, but your recent practice suggests retrieval needs strengthening."
        return f"Your strongest current knowledge cluster is {strongest}. Increase transfer practice to apply it in unfamiliar situations."

