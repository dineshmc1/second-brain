from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.database import Database, db
from app.models.schemas import LearningGoalCreate, LearningRun
from app.services.llm_service import LLMUnavailable, get_llm_service


MODE_PROMPTS = {
    "accelerate": "Act as an adaptive mastery tutor. Diagnose prior knowledge, teach only the missing idea, ask one retrieval question, and finish with one practical challenge.",
    "explain": "Explain for this learner using a plain-language model, an analogy, a concrete example, common confusion, and a two-question understanding check.",
    "misconception": "Analyze the learner's explanation. Separate correct reasoning from misconceptions, identify the root mental-model error, correct it, then give a discriminating test question.",
    "compress": "Compress the material without losing causal structure. Return: one-sentence thesis, five essential principles, disagreements or uncertainty, and a compact mental model.",
    "transfer": "Extract the underlying principle and transfer it to three distant domains. For each, explain the mapping, limits of the analogy, and one practical application.",
    "simulate": "Create an interactive decision simulation from the topic. Give role, objective, constraints, hidden risks, and the first decision point. Do not reveal the ideal solution yet.",
    "experts": "Convene a concise board: scientist, engineer, strategist, skeptic, teacher, and operator. Give each distinct analysis, then synthesize agreements, disagreements, and the next best test.",
    "communication": "Coach the communication. Score clarity, structure, audience fit, confidence, and persuasiveness from 0-100. Identify three specific improvements and provide a stronger rewrite that preserves meaning.",
}


class LearningService:
    def __init__(self, database: Database = db) -> None:
        self.db = database

    def goals(self) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            goals = [dict(row) for row in connection.execute("SELECT * FROM learning_goals ORDER BY updated_at DESC").fetchall()]
            for goal in goals:
                goal["nodes"] = [dict(row) for row in connection.execute(
                    "SELECT * FROM learning_nodes WHERE goal_id=? ORDER BY sequence", (goal["id"],)
                ).fetchall()]
        return goals

    def create_goal(self, payload: LearningGoalCreate) -> dict[str, Any]:
        goal_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        nodes, ai = self._compile_nodes(payload.title, payload.objective)
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO learning_goals(id,title,objective,status,progress,target_date,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (goal_id, payload.title, payload.objective, "active", 0, payload.target_date.isoformat() if payload.target_date else None, now, now),
            )
            previous_id = None
            for index, node in enumerate(nodes):
                node_id = str(uuid4())
                prerequisites = [previous_id] if previous_id else []
                connection.execute(
                    """INSERT INTO learning_nodes(id,goal_id,title,description,node_type,status,mastery,sequence,prerequisites_json,evidence_json,created_at,updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (node_id, goal_id, node["title"], node["description"], node.get("type", "concept"),
                     "ready" if index == 0 else "locked", 0, index, json.dumps(prerequisites), "[]", now, now),
                )
                previous_id = node_id
        goal = next(item for item in self.goals() if item["id"] == goal_id)
        goal["generated_with_ai"] = ai
        return goal

    def patch_node(self, node_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        changes = {key: value for key, value in changes.items() if value is not None and key in {"status", "mastery"}}
        changes["updated_at"] = datetime.now(UTC).isoformat()
        with self.db.transaction() as connection:
            row = connection.execute("SELECT goal_id FROM learning_nodes WHERE id=?", (node_id,)).fetchone()
            if not row:
                raise KeyError(node_id)
            assignments = ",".join(f"{key}=?" for key in changes)
            connection.execute(f"UPDATE learning_nodes SET {assignments} WHERE id=?", (*changes.values(), node_id))
            goal_id = row["goal_id"]
            stats = connection.execute(
                "SELECT AVG(mastery),SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END),COUNT(*) FROM learning_nodes WHERE goal_id=?",
                (goal_id,),
            ).fetchone()
            progress = round(float(stats[0] or 0), 1)
            connection.execute("UPDATE learning_goals SET progress=?,updated_at=? WHERE id=?", (progress, changes["updated_at"], goal_id))
            if changes.get("status") == "mastered":
                connection.execute(
                    """UPDATE learning_nodes SET status='ready' WHERE goal_id=? AND status='locked' AND sequence=(
                       SELECT MIN(sequence) FROM learning_nodes WHERE goal_id=? AND status='locked')""",
                    (goal_id, goal_id),
                )
            updated = connection.execute("SELECT * FROM learning_nodes WHERE id=?", (node_id,)).fetchone()
        return dict(updated)

    def run(self, payload: LearningRun) -> dict[str, Any]:
        system = MODE_PROMPTS[payload.mode] + " Be concise, concrete, and never pretend the learner demonstrated knowledge they did not demonstrate."
        max_tokens = {"quick": 320, "standard": 560, "deep": 850}[payload.depth]
        local = False
        try:
            result = get_llm_service().compact_response(payload.mode, system, payload.input, max_tokens=max_tokens)
            text = result["text"]
        except LLMUnavailable as exc:
            local = True
            result = {"cache_hit": False, "input_tokens": 0, "output_tokens": 0}
            text = self._local_response(payload.mode, payload.input, str(exc))
        misconceptions = self._extract_misconceptions(text) if payload.mode == "misconception" else []
        score = self._extract_score(text) if payload.mode == "communication" else None
        with self.db.transaction() as connection:
            connection.execute(
                """INSERT INTO learning_attempts(id,goal_id,node_id,mode,prompt,result,score,misconceptions_json,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (str(uuid4()), payload.goal_id, payload.node_id, payload.mode, payload.input, text, score,
                 json.dumps(misconceptions), datetime.now(UTC).isoformat()),
            )
        return {"result": text, "local": local, "misconceptions": misconceptions, "score": score, **result}

    def usage(self) -> dict[str, Any]:
        today = datetime.now(UTC).date().isoformat()
        with self.db.connect() as connection:
            row = connection.execute(
                """SELECT COUNT(*) calls,COALESCE(SUM(input_tokens),0) input_tokens,
                   COALESCE(SUM(output_tokens),0) output_tokens,COALESCE(SUM(cache_hit),0) cache_hits
                   FROM ai_usage WHERE substr(created_at,1,10)=?""", (today,)
            ).fetchone()
        return dict(row)

    def _compile_nodes(self, title: str, objective: str) -> tuple[list[dict[str, str]], bool]:
        prompt = (
            f"Goal: {title}\nOutcome: {objective}\n"
            "Create 6-8 ordered curriculum nodes. One per line exactly: Title | practical mastery evidence. "
            "Start with foundations, end with an authentic project."
        )
        try:
            response = get_llm_service().compact_response("curriculum", "You are a curriculum compiler. Output only the requested lines.", prompt, 420)
            nodes = []
            for line in response["text"].splitlines():
                clean = re.sub(r"^\s*[-*\d.)]+\s*", "", line).strip()
                if "|" not in clean:
                    continue
                node_title, description = [part.strip() for part in clean.split("|", 1)]
                if node_title and description:
                    nodes.append({"title": node_title[:160], "description": description[:500]})
            if len(nodes) >= 4:
                return nodes[:8], True
        except LLMUnavailable:
            pass
        subject = title.strip()
        return [
            {"title": f"Map {subject}", "description": "Define the outcome, core vocabulary, and what mastery looks like."},
            {"title": "Build foundations", "description": f"Learn the prerequisite concepts required to reason about {subject}."},
            {"title": "Explain the core model", "description": "Explain the central ideas from memory using your own examples."},
            {"title": "Guided practice", "description": "Solve representative problems with immediate feedback."},
            {"title": "Transfer practice", "description": "Apply the principles to a new and unfamiliar context."},
            {"title": "Authentic project", "description": f"Produce a real artifact that demonstrates the objective: {objective[:220]}"},
            {"title": "Retention check", "description": "Reconstruct the key ideas later without notes and repair weak areas."},
        ], False

    @staticmethod
    def _local_response(mode: str, text: str, reason: str) -> str:
        topic = " ".join(text.strip().split())[:500]
        templates = {
            "accelerate": f"Diagnostic: explain what you already know about **{topic}** in three sentences.\n\nThen answer: what result would prove you can use it?\n\nPractical challenge: create one small example without referring to notes.",
            "explain": f"Start with the simplest useful question: what problem does **{topic}** solve? Break it into inputs, transformation, and output. Create one concrete example, then test yourself by changing one assumption.",
            "misconception": f"Separate your statement into claims and evidence. For **{topic}**, mark each claim as observed, inferred, or assumed. The likely risk is treating an assumption as evidence. Test it with a counterexample.",
            "compress": f"Compression target: **{topic}**\n\n1. State the governing idea in one sentence.\n2. Keep only causes, constraints, and consequences.\n3. Remove repeated examples.\n4. Record uncertainty explicitly.",
            "transfer": f"Extract the rule behind **{topic}**, then test it in: a physical system, a social system, and a software system. Record where the analogy breaks.",
            "simulate": f"Simulation: you must use **{topic}** under time pressure. Define your objective, three constraints, and the first irreversible decision. What do you do first, and what evidence would change your choice?",
            "experts": f"Scientist: what evidence supports **{topic}**?\nEngineer: what can be tested cheaply?\nStrategist: what compounds over time?\nSkeptic: which assumption is weakest?\nTeacher: can you explain it plainly?\nOperator: what is the next observable action?",
            "communication": f"Review **{topic}** for one central message, logical order, audience relevance, and unnecessary words. Rewrite it as: context -> main point -> evidence -> requested action.",
        }
        return templates[mode] + f"\n\n_Local mode used: {reason}_"

    @staticmethod
    def _extract_misconceptions(text: str) -> list[str]:
        matches = re.findall(r"(?:misconception|incorrect assumption|mental-model error)\s*[:\-]\s*([^\n]+)", text, re.I)
        return [match.strip()[:200] for match in matches[:5]]

    @staticmethod
    def _extract_score(text: str) -> float | None:
        match = re.search(r"(?:overall|score)[^\d]{0,8}(\d{1,3})(?:\s*/\s*100|%)?", text, re.I)
        return min(float(match.group(1)), 100) if match else None

