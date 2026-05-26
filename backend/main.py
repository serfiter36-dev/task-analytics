from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
from typing import Optional
from models import TasksResponse, StatsResponse
from analyzer import analyze_tasks

app = FastAPI(title="Task Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при деплое заменить на URL фронтенда
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Task Analytics API"}


@app.post("/api/upload", response_model=TasksResponse)
async def upload_file(file: UploadFile = File(...)):
    """Принимает .xlsx или .csv, возвращает список задач + статистику."""
    if not file.filename.endswith((".xlsx", ".csv")):
        raise HTTPException(400, "Поддерживаются только .xlsx и .csv файлы")

    content = await file.read()

    try:
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(422, f"Не удалось прочитать файл: {e}")

    return analyze_tasks(df)


@app.post("/api/analyze-complexity")
async def analyze_complexity(payload: dict):
    import os, json, httpx
    tasks = payload.get("tasks", [])
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "GEMINI_API_KEY не задан в файле backend/.env")

    BATCH_SIZE = 25
    results = []

    async with httpx.AsyncClient(timeout=120) as client:
        for i in range(0, len(tasks), BATCH_SIZE):
            batch = tasks[i:i+BATCH_SIZE]
            batch_data = [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "description": (t.get("description") or "")[:800]
                }
                for t in batch
            ]

            prompt = f"""Оцени сложность каждой задачи для команды разработчиков 1С.
Верни ТОЛЬКО валидный JSON массив без markdown, без пояснений, без текста до или после.

Критерии сложности:
- Лёгкая: косметические правки UI, скрыть/показать поле, права доступа, переименование, добавить простой реквизит
- Средняя: новый отчёт, доработка формы, простая обработка данных, добавление функционала в существующий объект
- Сложная: новый функциональный блок, интеграция систем, сложная бизнес-логика, переделка существующего механизма
- Очень сложная: архитектурные изменения, критические баги в проде с неясной причиной, многоэтапные доработки затрагивающие несколько подсистем

Задачи для оценки:
{json.dumps(batch_data, ensure_ascii=False)}

Ответь строго в формате JSON массива (без лишнего текста):
[{{"id": "EVR-001", "complexity": "Средняя", "reason": "Одно предложение обоснования на русском"}}]"""

            try:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 4000,
                            "responseMimeType": "application/json"
                        }
                    }
                )
                resp.raise_for_status()
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                batch_results = json.loads(text.strip())
                results.extend(batch_results)
            except json.JSONDecodeError:
                for t in batch:
                    results.append({"id": t["id"], "complexity": "Средняя", "reason": "Ошибка парсинга ответа AI"})
            except Exception as e:
                for t in batch:
                    results.append({"id": t["id"], "complexity": "Средняя", "reason": f"Ошибка: {str(e)}"})

    return {"results": results}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
