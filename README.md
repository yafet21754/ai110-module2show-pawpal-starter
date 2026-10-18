# 🐾 PawPal+

A CLI-first, object-oriented pet care manager with a Streamlit dashboard. Track care for multiple pets, organize a daily schedule, complete recurring tasks, and select tasks within an available care-time budget.

## Features

- Owner and pet profiles; multiple pets in one household.
- Add and edit care tasks with date, time, duration, priority, and recurrence.
- Chronological schedules and combined pet/status/date filters.
- Daily and weekly recurrence with completed-occurrence history.
- Same-time warnings across the whole household.
- Priority-based time-budget plans with selection explanations.
- Session state retains objects across Streamlit reruns.

## Setup

Requires Python 3.10 or newer. Open this folder in VS Code, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
python -m streamlit run app.py
```

Windows PowerShell activation: `.\.venv\Scripts\Activate.ps1`.
Open the local URL shown by Streamlit. Stop the server with Ctrl+C.

## Implementation summary

`pawpal_system.py` contains four classes. `Owner` manages `Pet` objects and exposes `get_all_tasks()`, which returns pet/task pairs from every pet. `Pet` stores `Task` dataclasses. `Scheduler` reads through the owner method for every scheduling operation. `app.py` imports all four classes and stores its owner in `st.session_state`; forms call the backend directly. `main.py` runs the same backend without the UI.

`Task.mark_complete()` changes status only. Use `Scheduler.mark_task_complete(task_id)` in application workflows so daily and weekly recurrence is created as well. Repeating that scheduler call on a completed occurrence does not create duplicates.

## Smarter Scheduling

| Feature | Method | Behavior |
| --- | --- | --- |
| Sorting | `Scheduler.sort_by_time()` | Orders by date and HH:MM time; does not mutate task lists. |
| Filtering | `Scheduler.filter_tasks()` | Combines optional pet name, completion status, and due date. |
| Conflict warnings | `Scheduler.detect_conflicts()` | Groups pending tasks with the exact same date/time, including different pets. |
| Recurrence | `Scheduler.mark_task_complete()` | Adds an independent pending occurrence one or seven days after the scheduled date. |
| Time budget | `Scheduler.build_daily_plan()` | Greedily tries high, medium, then low priority; earlier times break ties; skips tasks that do not fit. |

Sorting costs O(n log n); filtering and recurrence lookup cost O(n). Conflict grouping costs O(n), plus O(k log k) to sort k timestamps. Budget selection costs O(n log n).

The budget is total care minutes, not a calendar availability window. Start times stay fixed, and conflict warnings remain advisory. Durations that overlap with different start times are not detected. Missed recurring occurrences advance from their original scheduled date to preserve cadence. Data is in memory for the browser session; a new session or server restart does not retain it. Local dates are used; time-zone handling and shared accounts are outside this version.

## Demo Walkthrough

1. Add Mochi (dog) and Luna (cat) using the sidebar. You may also update the owner name.
2. Schedule Mochi's Breakfast at 08:00 today, 10 minutes, high priority, daily. Add Luna's Medication at 08:00, 5 minutes, high priority, weekly. Add Playtime at 12:30 and Evening walk at 18:00.
3. View today's schedule. Tasks appear chronologically even if entered out of order. An 08:00 conflict warning names both pets and tasks.
4. Choose a pet or status to filter the schedule. Household conflict warnings remain visible so a filter cannot hide another pet's competing care task.
5. Select Breakfast and click **Mark complete**. The original becomes complete. Change the view date to tomorrow to see its new pending daily occurrence. Weekly tasks advance seven days when completed.
6. Expand **Edit a pending task** to change its description, date, time, duration, priority, or frequency. Completed history cannot be edited in this UI.
7. Enter a 15-minute budget. With the example tasks pending, Breakfast and Medication fit first. The app explains the priority rule and lists tasks left outside the budget. Complete Breakfast after trying this plan if you want that exact selection.

### Sample Output

Actual CLI output from `python main.py` (dates follow the execution day):

```text
Today's Schedule
08:00 | Mochi | Breakfast    | 10 min | high
08:00 | Luna  | Medication   |  5 min | high
12:30 | Luna  | Playtime     | 20 min | medium
18:00 | Mochi | Evening walk | 30 min | low
WARNING: 2026-10-18 08:00 conflict: Mochi: Breakfast / Luna: Medication
Pending Luna tasks: 2
15-minute plan: Breakfast, Medication
Breakfast completed: True
Next breakfast: 2026-10-19 at 08:00 (pending)
```

## Testing PawPal+

```bash
python -m pytest
```

Tests cover task addition/completion, cross-pet/date sorting, filters, recurrence and duplicate completion, conflicts, empty data, invalid inputs, and time budgets. Two Streamlit AppTest scenarios verify forms, edits, completion, state across reruns, filters, and conflict warnings.

Actual successful run:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.14, pytest-9.1.1, pluggy-1.7.0
rootdir: /workspace/scratch/9758f2563c9e/pawpal-plus
plugins: anyio-4.15.1
collected 25 items

tests/test_app.py ..                                                     [  8%]
tests/test_pawpal.py .......................                             [100%]

============================== 25 passed in 1.18s ==============================
```

Confidence level: ★★★★☆ (4/5). These tests verify covered backend and UI interactions; they do not establish production reliability or a full visual browser audit.

## Architecture and project files

- `diagrams/uml_draft.mmd`: original four-class blueprint.
- `diagrams/uml_final.mmd`: final fields, methods, and relationships.
- `pawpal_system.py`: validated backend and scheduling algorithms.
- `main.py`: reproducible CLI demonstration.
- `app.py`: Streamlit dashboard.
- `tests/test_pawpal.py`: backend verification.
- `tests/test_app.py`: Streamlit interaction verification.
- `reflection.md`: structured reflection draft, with honest AI-workflow details.
- `ai_interactions.md`: record of assistance actually used.

## Before submitting

Review and personalize the reflection, run the app locally, publish all files and meaningful commits to your public fork, and submit that repository URL through the course. GitHub publishing and course submission have not been performed in this package.

Starter: https://github.com/codepath/ai110-module2show-pawpal-starter
