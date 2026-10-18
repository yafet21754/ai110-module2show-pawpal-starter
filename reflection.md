# PawPal+ Project Reflection

**Review draft:** This describes the implementation and verification performed with ChatGPT/Codex. Yafet should review the code, run it locally, and adapt the personal learning statements before submitting. No separate chat sessions or manual VS Code work are claimed.

## 1. System Design

### a. Initial design
Three core user actions are: (1) add multiple pets to a household, (2) schedule care tasks such as feeding, walks, and medication, and (3) view a day's tasks and mark them complete.

The initial UML has four classes. Owner holds the household's pets and collects every pet's tasks. Pet holds a name, species, and task list. Task holds a description, time, date, frequency, and completion status. Scheduler gets the combined task list from Owner and organizes it. Pet and Task use dataclasses, and Owner also uses a dataclass to reduce repeated initialization code.

### b. Design changes
The final Task includes duration, priority, and a unique task ID. Duration and priority support a limited care-time budget. IDs distinguish repeated tasks with identical descriptions and times. The final Scheduler adds filters, conflicts, recurrence, and a daily plan. Its methods retain pet/task pairs, so combining pets does not lose ownership information. A completed occurrence stays in history, and the scheduler adds a new pending occurrence instead of resetting the original task.

## 2. Scheduling Logic and Tradeoffs

### a. Constraints and priorities
The schedule considers date, time, completion status, pet, priority, and duration. The time-budget plan considers pending tasks on a chosen date, tries high priorities first, uses earlier times as a tie-breaker, and selects each task that fits the remaining budget. It displays selected tasks chronologically and explains skipped tasks. It does not change their chosen times. Exact start-time conflicts are shown separately and do not crash the app.

### b. Tradeoffs
Conflict detection groups equal date/time values. This is readable and takes linear time to group tasks, plus sorting the unique timestamps for chronological warnings. It does not detect overlapping durations. For example, 08:00 for 30 minutes and 08:15 for 10 minutes will not produce a warning. This is a reasonable minimum implementation but a limitation for a busy household.

The priority algorithm is greedy rather than an optimal knapsack solver. It may leave some minutes unused or select fewer tasks than another combination, but its decisions are easy to explain. Recurrence advances from the original scheduled date by one or seven days; completing an overdue task can therefore create another overdue occurrence. That preserves the intended cadence instead of silently skipping missed care.

## 3. AI Collaboration

### a. How AI was used
The user supplied the assignment and asked ChatGPT/Codex to complete it. The assistant inspected the starter, wrote a UML draft and class skeletons, implemented the backend, connected Streamlit forms, wrote tests, and ran the CLI and test suite. Automatic file editing and terminal execution were the most useful features because the assistant could verify the implementation instead of only suggesting snippets.

The assignment supplied useful context for the work: four required classes, a multi-pet owner method, exact test behaviors, and required documentation. This is an example of context engineering: giving AI concrete constraints and expected evidence. Future follow-up prompts could ask, "Explain why completing the same recurring task twice must not create two future tasks" or "Trace how the UI reaches Owner.get_all_tasks through Scheduler."

The work used one conversation with distinct design, backend, UI, and testing stages. Separate chat sessions were not used, so their benefits were not directly evaluated. For a future iteration, focused sessions could reduce unrelated context, but each would still need the current files and requirements.

### b. Judgment and verification
An implementation choice made by the assistant was to keep recurrence in Scheduler.mark_task_complete rather than put pet-list mutation inside Task.mark_complete. Task can update its own status without knowing its parent pet; Scheduler can locate the pet and add the next occurrence. A guard prevents repeat completion from creating duplicate future tasks. This was verified by daily and weekly tests.

This was the assistant's design decision, not a documented personal rejection by Yafet. Before submission, Yafet should inspect an AI suggestion, decide whether to accept or modify it, and record that actual example here if the course requires a personal rejection example.

## 4. Testing and Verification

### a. What was tested
The suite verifies task completion and addition, chronology across pets and dates, unchanged stored order, combined filters, daily and weekly recurrence across a year boundary, repeat-completion safety, one-time tasks, same-pet and cross-pet conflicts, completed-task exclusions, empty schedules, priority budgets, and invalid inputs.

Two Streamlit AppTest tests exercise the app itself: adding pets and tasks, editing, completing a daily task, viewing the next occurrence, changing filters, retaining state across reruns, and presenting conflict warnings. These checks matter because a correct backend does not guarantee the form buttons call it correctly.

The recorded result is 25 passing tests. The CLI also prints a sorted two-pet schedule, a real conflict warning, filtered counts, a constrained plan, and the next daily occurrence.

### b. Confidence
Implementation confidence: 4/5. Covered behaviors pass automated verification, including the UI harness. This is not a claim of production readiness. Future checks should cover browser visual layout on mobile, time zones, daylight saving changes, overlapping durations, and multiple people editing shared data.

## 5. Reflection

### a. What went well
The implementation keeps backend behavior independent of Streamlit. The same Scheduler serves the CLI, app, and tests. The UML shows the final relationships, and the README includes actual execution evidence.

### b. What could improve
Add durable storage so care history survives a new session or server restart. Then add overlap detection, recurring-series editing, and explicit handling of missed recurring tasks. Currently editing a pending occurrence affects its future recurrence but does not rewrite other existing occurrences.

### c. Key takeaway
A lead architect must connect requirements, class responsibilities, and verification. AI can generate working code quickly, but the human still needs to understand the algorithm and evaluate its trade-offs. A UML diagram is useful when it stays aligned with code, and verification requires checking real behavior instead of trusting generated output.
