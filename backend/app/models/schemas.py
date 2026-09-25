from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MemoryType(StrEnum):
    SEMANTIC = "semantic"
    PERSONAL = "personal"
    EPISODIC = "episodic"
    DOCUMENT = "document"
    DECISION = "decision"
    PROJECT = "project"
    TASK = "task"
    PEOPLE = "people"
    CONVERSATION = "conversation"


class MemoryOperation(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CONFIRM = "CONFIRM"
    SUPERSEDE = "SUPERSEDE"
    MERGE = "MERGE"
    IGNORE = "IGNORE"


class MemoryExtract(BaseModel):
    should_store: bool = True
    operation: MemoryOperation = MemoryOperation.CREATE
    memory_type: MemoryType = MemoryType.SEMANTIC
    title: str = Field(min_length=1, max_length=160)
    fact: str = Field(min_length=1)
    entity: str | None = None
    property_key: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    importance: float = Field(default=0.6, ge=0, le=1)
    confidence: float = Field(default=0.8, ge=0, le=1)
    effective_from: datetime | None = None
    possible_conflicts: list[str] = Field(default_factory=list)


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1)
    memory_type: MemoryType | None = None
    title: str | None = None
    entity: str | None = None
    property_key: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    project_id: str | None = None
    source_type: str = "manual"
    importance_score: float = Field(default=0.6, ge=0, le=1)
    confidence_score: float = Field(default=0.9, ge=0, le=1)


class MemoryPatch(BaseModel):
    title: str | None = None
    content: str | None = None
    memory_type: MemoryType | None = None
    category: str | None = None
    tags: list[str] | None = None
    project_id: str | None = None
    importance_score: float | None = Field(default=None, ge=0, le=1)
    status: Literal["current", "historical", "superseded", "deleted", "uncertain"] | None = None


class MemoryOut(BaseModel):
    id: str
    memory_type: str
    title: str
    content: str
    normalized_fact: str
    entity: str | None
    property_key: str | None
    category: str | None
    tags: list[str]
    source_type: str
    source_id: str | None
    project_id: str | None
    created_at: datetime
    updated_at: datetime
    effective_from: datetime | None
    effective_until: datetime | None
    importance_score: float
    confidence_score: float
    status: str
    supersedes_memory_id: str | None
    metadata: dict[str, Any]


class Citation(BaseModel):
    id: str
    source_type: str
    label: str
    page: int | None = None
    excerpt: str
    score: float = 0


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=30_000)
    conversation_id: str | None = None
    project_id: str | None = None
    response_mode: Literal["text", "voice", "both"] = "text"


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    retrieved_memory_ids: list[str]
    conversation_id: str
    memory_action: str | None = None
    offline: bool = False


class SearchResult(BaseModel):
    id: str
    kind: Literal["memory", "chunk", "file", "project"]
    title: str
    excerpt: str
    score: float
    source_type: str
    page: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    color: str = "#68e8ff"


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    goal: str | None = None
    status: Literal["active", "paused", "completed", "archived"] | None = None


class InboxCreate(BaseModel):
    content: str = Field(min_length=1, max_length=30_000)
    source_type: str = "capture"


class InboxProcess(BaseModel):
    action: Literal["memory", "task", "project", "archive", "discard"]
    project_id: str | None = None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str = ""
    status: Literal["backlog", "next", "in_progress", "blocked", "done"] = "backlog"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    due_at: datetime | None = None
    project_id: str | None = None
    parent_task_id: str | None = None


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = None
    status: Literal["backlog", "next", "in_progress", "blocked", "done"] | None = None
    priority: Literal["low", "medium", "high", "critical"] | None = None
    due_at: datetime | None = None
    project_id: str | None = None
    position: int | None = Field(default=None, ge=0)


class TaskBreakdown(BaseModel):
    title: str = Field(min_length=1, max_length=2000)
    project_id: str | None = None


class LearningGoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=4000)
    target_date: datetime | None = None


class LearningNodePatch(BaseModel):
    status: Literal["locked", "ready", "learning", "mastered"] | None = None
    mastery: float | None = Field(default=None, ge=0, le=100)


class LearningRun(BaseModel):
    mode: Literal["accelerate", "explain", "misconception", "compress", "transfer", "simulate", "experts", "communication"]
    input: str = Field(min_length=1, max_length=30_000)
    goal_id: str | None = None
    node_id: str | None = None
    depth: Literal["quick", "standard", "deep"] = "standard"


class SettingUpdate(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
    api_key: str | None = None
    calendar_url: str | None = None
