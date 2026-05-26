from dotenv import load_dotenv
load_dotenv()

import sys
sys.stdout.reconfigure(encoding='utf-8')

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
    sys.stdout.write(f"=== ANALYZE CALLED: {len(tasks)} tasks ===\n")
    sys.stdout.flush()
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(500, "GEMINI_API_KEY не задан в файле backend/.env")

    BATCH_SIZE = 10
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
                sys.stdout.write(f"=== SENDING BATCH {i//10 + 1}, tasks: {len(batch)} ===\n")
                sys.stdout.flush()
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 8000,
                            "thinkingConfig": {"thinkingBudget": 0}
                        }
                    }
                )
                sys.stdout.write(f"=== HTTP STATUS: {resp.status_code} ===\n")
                sys.stdout.flush()
                sys.stdout.write(f"=== RESP BODY START: {resp.text[:200]} ===\n")
                sys.stdout.flush()
                resp.raise_for_status()
                raw_response = resp.json()
                import json as json_module
                sys.stdout.write("=== FULL GEMINI RESPONSE ===\n")
                sys.stdout.write(json_module.dumps(raw_response, ensure_ascii=False, indent=2)[:1000] + "\n")
                sys.stdout.write("===========================\n")
                sys.stdout.flush()
                text = raw_response["candidates"][0]["content"]["parts"][0]["text"].strip()
                sys.stdout.write("=== TEXT TO PARSE ===\n")
                sys.stdout.write(repr(text[:500]) + "\n")
                sys.stdout.write("=====================\n")
                sys.stdout.flush()
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                batch_results = json.loads(text.strip())
                results.extend(batch_results)
            except Exception as e:
                sys.stdout.write(f"=== EXCEPTION: {type(e).__name__}: {str(e)[:200]} ===\n")
                sys.stdout.flush()
                safe_msg = str(e).replace(api_key, "***")
                for t in batch:
                    results.append({"id": t["id"], "complexity": "Средняя", "reason": f"Ошибка: {safe_msg}"})

    return {"results": results}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
