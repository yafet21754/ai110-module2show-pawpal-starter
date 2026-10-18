"""CLI-first demonstration with two pets and deliberately unordered tasks."""
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    """Show sorting, filtering, conflicts, priorities, and recurrence."""
    today = date.today()
    owner = Owner('Jordan')
    mochi, luna = Pet('Mochi', 'dog'), Pet('Luna', 'cat')
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task('Evening walk', '18:00', today, duration_minutes=30, priority='low'))
    breakfast = Task('Breakfast', '08:00', today, 'daily', 10, 'high')
    mochi.add_task(breakfast)
    luna.add_task(Task('Medication', '08:00', today, 'weekly', 5, 'high'))
    luna.add_task(Task('Playtime', '12:30', today, duration_minutes=20))
    scheduler = Scheduler(owner)
    print("Today's Schedule")
    for pet, task in scheduler.sort_by_time(due_date=today):
        print(f'{task.time} | {pet.name:5} | {task.description:12} | {task.duration_minutes:2} min | {task.priority}')
    for warning in scheduler.detect_conflicts(today):
        print('WARNING:', warning)
    print('Pending Luna tasks:', len(scheduler.filter_tasks('Luna', False, today)))
    plan = scheduler.build_daily_plan(today, 15)
    print('15-minute plan:', ', '.join(t.description for _, t in plan['selected']))
    following = scheduler.mark_task_complete(breakfast.task_id)
    print('Breakfast completed:', breakfast.completed)
    print(f'Next breakfast: {following.due_date} at {following.time} (pending)')


if __name__ == '__main__':
    main()
