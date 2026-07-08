from pydantic import BaseModel
from typing import Optional


class Task(BaseModel):
    id: str
    title: str
    author: str
    assignee: str
    created: Optional[str]
    completed: Optional[str]
    deadline: Optional[str]
    days: Optional[int]
    is_bug: bool
    description: str = ""
    complexity: str = ""
    reason: str = ""
    project: str = "Евро"
    func_group: str = ""
    support_line: str = ""


class AssigneeStats(BaseModel):
    name: str
    total: int
    avg_days: Optional[float]


class AuthorStats(BaseModel):
    name: str
    total: int


class WeekStats(BaseModel):
    week: str
    count: int


class Summary(BaseModel):
    total: int
    avg_days: float
    min_days: int
    max_days: int
    bugs_count: int
    no_deadline: int
    available_months: list[str]


class StatsResponse(BaseModel):
    summary: Summary
    by_assignee: list[AssigneeStats]
    by_author: list[AuthorStats]
    by_week: list[WeekStats]
    available_months: list[str]


class TasksResponse(BaseModel):
    tasks: list[Task]
    stats: StatsResponse
