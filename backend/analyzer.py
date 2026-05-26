import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from models import (
    Task, AssigneeStats, AuthorStats, WeekStats,
    Summary, StatsResponse, TasksResponse
)

# Маппинг возможных названий колонок → стандартные имена
COLUMN_MAP = {
    # ID
    "id задачи": "id",
    "task id": "id",
    "id": "id",
    # Название
    "название задачи": "title",
    "название": "title",
    "title": "title",
    "name": "title",
    # Автор
    "автор": "author",
    "author": "author",
    # Исполнитель
    "исполнитель / менеджер": "assignee",
    "исполнитель": "assignee",
    "assignee": "assignee",
    "assigned_to": "assignee",
    # Дата создания
    "создана": "created",
    "created_at": "created",
    "created": "created",
    # Дата выполнения
    "дата выполнения": "completed",
    "completed_at": "completed",
    "completed": "completed",
    "closed_at": "completed",
    # Дедлайн
    "дедлайн": "deadline",
    "due_date": "deadline",
    "deadline": "deadline",
    # Игнорируемые колонки (не нужны для анализа)
    "описание задачи": "description",
    "description": "description",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Приводим названия колонок к стандартному виду."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    rename = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            rename[col] = COLUMN_MAP[col]
    return df.rename(columns=rename)


def parse_date(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "nat", ""):
        return None
    # Пробуем точное совпадение — без обрезки строки
    for fmt in [
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Если в строке есть лишнее — пробуем взять только первые 16/10 символов
    for s_cut, fmt in [
        (s[:16], "%d.%m.%Y %H:%M"),
        (s[:10], "%d.%m.%Y"),
        (s[:10], "%Y-%m-%d"),
    ]:
        try:
            return datetime.strptime(s_cut, fmt)
        except ValueError:
            continue
    return None


def fmt_date(d: datetime | None) -> str | None:
    return d.strftime("%Y-%m-%d") if d else None


def analyze_tasks(df: pd.DataFrame) -> TasksResponse:
    df = normalize_columns(df)

    tasks = []
    assignee_map = defaultdict(lambda: {"total": 0, "days": []})
    author_map = defaultdict(int)
    week_map = defaultdict(int)

    for idx, row in df.iterrows():
        task_id = str(row.get("id", f"TASK-{idx+1}") or "").strip()
        title = str(row.get("title", "") or "").strip()
        author = str(row.get("author", "") or "").strip()
        assignee = str(row.get("assignee", "") or "").strip()

        if not task_id or not title:
            continue

        created = parse_date(row.get("created"))
        completed = parse_date(row.get("completed"))
        deadline = parse_date(row.get("deadline"))

        days = None
        if created and completed:
            days = (completed - created).days

        is_bug = any(kw in title.upper() for kw in [
            "ОШИБК", "ERROR", "BUG", "БАГИ", "В РАБОЧЕЙ", "В ПРОДЕ"
        ])

        # Статистика по исполнителям (каждый упомянутый)
        for a in assignee.split(","):
            a = a.strip()
            if a:
                assignee_map[a]["total"] += 1
                if days is not None:
                    assignee_map[a]["days"].append(days)

        if author:
            author_map[author] += 1

        if completed:
            monday = completed - timedelta(days=completed.weekday())
            week_key = monday.strftime("%d.%m")
            week_map[week_key] += 1

        tasks.append(Task(
            id=task_id,
            title=title,
            author=author,
            assignee=assignee,
            created=fmt_date(created),
            completed=fmt_date(completed),
            deadline=fmt_date(deadline),
            days=days,
            is_bug=is_bug,
        ))

    all_days = [t.days for t in tasks if t.days is not None]
    bugs = sum(1 for t in tasks if t.is_bug)
    no_deadline = sum(1 for t in tasks if not t.deadline)

    summary = Summary(
        total=len(tasks),
        avg_days=round(sum(all_days) / len(all_days), 1) if all_days else 0,
        min_days=min(all_days) if all_days else 0,
        max_days=max(all_days) if all_days else 0,
        bugs_count=bugs,
        no_deadline=no_deadline,
    )

    by_assignee = sorted([
        AssigneeStats(
            name=name,
            total=data["total"],
            avg_days=round(sum(data["days"]) / len(data["days"]), 1) if data["days"] else None,
        )
        for name, data in assignee_map.items()
    ], key=lambda x: -x.total)

    by_author = sorted([
        AuthorStats(name=name, total=cnt)
        for name, cnt in author_map.items()
    ], key=lambda x: -x.total)

    by_week = [
        WeekStats(week=week, count=cnt)
        for week, cnt in sorted(week_map.items())
    ]

    return TasksResponse(
        tasks=tasks,
        stats=StatsResponse(
            summary=summary,
            by_assignee=by_assignee,
            by_author=by_author,
            by_week=by_week,
        )
    )
