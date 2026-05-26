# Task Analytics

Веб-приложение для анализа выгрузок из таск-менеджеров.  
Загружаешь `.xlsx` или `.csv` → получаешь статистику, графики, лидерборд.

## Структура проекта

```
task-analytics/
├── backend/
│   ├── main.py          # FastAPI приложение
│   ├── analyzer.py      # Логика анализа данных
│   ├── models.py        # Pydantic-модели
│   └── requirements.txt
├── frontend/
│   └── index.html       # SPA (один файл, деплоится на GitHub Pages)
└── README.md
```

---

## Локальный запуск

### 1. Бэкенд

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API будет доступен на `http://localhost:8000`  
Документация: `http://localhost:8000/docs`

### 2. Фронтенд

Открой `frontend/index.html` в браузере.  
В файле найди строку:

```js
const API_URL = "https://YOUR-APP.onrender.com";
```

Для локальной разработки замени на:

```js
const API_URL = "http://localhost:8000";
```

---

## Деплой

### Бэкенд → Render.com (бесплатно)

1. Зарегистрируйся на [render.com](https://render.com)
2. New → **Web Service** → подключи этот репозиторий
3. Настройки:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. После деплоя скопируй URL вида `https://task-analytics-xxxx.onrender.com`

### Фронтенд → GitHub Pages

1. В `frontend/index.html` замени `API_URL` на URL из Render
2. Закоммить и запушить изменения
3. В репозитории: **Settings → Pages → Source: main, /frontend**
4. Сайт будет на `https://ВАШ-ЛОГИН.github.io/task-analytics/`

---

## Ожидаемые колонки в файле

| Колонка | Варианты названий |
|---|---|
| ID задачи | `id`, `id задачи`, `task id` |
| Название | `title`, `название`, `название задачи` |
| Автор | `author`, `автор` |
| Исполнитель | `assignee`, `исполнитель`, `исполнитель / менеджер` |
| Дата создания | `created`, `created_at`, `создана` |
| Дата выполнения | `completed`, `completed_at`, `closed_at`, `дата выполнения` |
| Дедлайн | `deadline`, `due_date`, `дедлайн` |

Форматы дат: `dd.mm.yyyy hh:mm`, `dd.mm.yyyy`, `yyyy-mm-dd`

---

## Доработка

### Добавить новую метрику

В `backend/analyzer.py` добавь расчёт в функцию `analyze_tasks()`,  
в `backend/models.py` добавь поле в `Summary`,  
в `frontend/index.html` добавь карточку в `renderMetrics()`.

### Добавить новый график

В `frontend/index.html` добавь `<canvas>` в нужный таб и вызов `new Chart(...)` в `renderCharts()`.

### Изменить логику определения ошибок

В `backend/analyzer.py` найди строку:
```python
is_bug = any(kw in title.upper() for kw in ["ОШИБК", "ERROR", "BUG", ...])
```
