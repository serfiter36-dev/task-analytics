import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from analyzer import analyze_tasks

TEST_FILE = "test_data.xlsx"

if os.path.exists(TEST_FILE):
    df = pd.read_excel(TEST_FILE)
    print(f"Читаю файл: {TEST_FILE}")
else:
    df = pd.DataFrame([{
        "Описание задачи": "",
        "ID задачи": "EVR-001",
        "Название задачи": "Тест задача",
        "Создана": "21.05.2026 14:26",
        "Автор": "Иван",
        "Исполнитель / Менеджер": "Иван, Петр",
        "Дедлайн": "",
        "Дата выполнения": "22.05.2026 15:41",
    }])
    print("Файл не найден — использую тестовый DataFrame")

result = analyze_tasks(df)

if not result.tasks:
    print("ОШИБКА: tasks пустой")
    sys.exit(1)

t = result.tasks[0]
print(f"\n--- Первая задача ---")
print(f"id:        {t.id}")
print(f"title:     {t.title}")
print(f"author:    {t.author}")
print(f"assignee:  {t.assignee}")
print(f"created:   {t.created}")
print(f"completed: {t.completed}")
print(f"deadline:  {t.deadline}")
print(f"days:      {t.days}")
print(f"is_bug:    {t.is_bug}")
