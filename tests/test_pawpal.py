from datetime import date, timedelta
import pytest
from pawpal_system import Owner, Pet, Task, Scheduler

DAY = date(2026, 10, 18)

@pytest.fixture
def household():
    owner = Owner('Jordan')
    a, b = Pet('Mochi', 'dog'), Pet('Luna', 'cat')
    owner.add_pet(a)
    owner.add_pet(b)
    return owner, a, b, Scheduler(owner)


def test_task_completion():
    task = Task('Walk', '08:00')
    task.mark_complete()
    assert task.completed is True


def test_task_addition():
    pet = Pet('Mochi', 'dog')
    task = Task('Walk', '08:00')
    pet.add_task(task)
    assert pet.tasks == [task]


def test_sort_across_pets_and_dates_without_mutation(household):
    owner, a, b, s = household
    late = Task('Walk', '18:00', DAY)
    early = Task('Food', '07:00', DAY)
    tomorrow = Task('Vet', '06:00', DAY + timedelta(days=1))
    a.add_task(late)
    a.add_task(early)
    b.add_task(tomorrow)
    assert [t for _, t in s.sort_by_time()] == [early, late, tomorrow]
    assert a.tasks == [late, early]
    assert len(owner.get_all_tasks()) == 3


def test_combined_filters(household):
    _, a, b, s = household
    a.add_task(Task('Food', '08:00', DAY))
    b.add_task(Task('Food', '08:00', DAY, completed=True))
    b.add_task(Task('Vet', '08:00', DAY + timedelta(days=1)))
    assert s.filter_tasks('luna', True, DAY) == [(b, b.tasks[0])]
    assert len(s.filter_tasks(completed=False)) == 2


@pytest.mark.parametrize('frequency,days', [('daily', 1), ('weekly', 7)])
def test_recurrence_and_repeat_completion(household, frequency, days):
    _, a, _, s = household
    original = Task('Food', '08:00', date(2026, 12, 31), frequency, 10, 'high')
    a.add_task(original)
    next_task = s.mark_task_complete(original.task_id)
    assert original.completed
    assert next_task.due_date == original.due_date + timedelta(days=days)
    assert not next_task.completed
    assert next_task.task_id != original.task_id
    assert (next_task.description, next_task.time, next_task.frequency,
            next_task.duration_minutes, next_task.priority) == ('Food', '08:00', frequency, 10, 'high')
    assert s.mark_task_complete(original.task_id) is None
    assert len(a.tasks) == 2


def test_once_does_not_recur(household):
    _, a, _, s = household
    t = Task('Vet', '12:00', DAY)
    a.add_task(t)
    assert s.mark_task_complete(t.task_id) is None
    assert len(a.tasks) == 1


def test_conflict_across_pets_ignores_other_dates_and_completed(household):
    _, a, b, s = household
    a.add_task(Task('Food', '08:00', DAY))
    b.add_task(Task('Walk', '08:00', DAY))
    b.add_task(Task('Vet', '08:00', DAY + timedelta(days=1)))
    b.add_task(Task('Old', '08:00', DAY, completed=True))
    warnings = s.detect_conflicts(DAY)
    assert len(warnings) == 1
    assert 'Mochi: Food' in warnings[0] and 'Luna: Walk' in warnings[0]
    assert 'Old' not in warnings[0] and 'Vet' not in warnings[0]
    s.mark_task_complete(a.tasks[0].task_id)
    assert s.detect_conflicts(DAY) == []


def test_same_pet_conflict(household):
    _, a, _, s = household
    for title in ['Food', 'Walk', 'Medicine']:
        a.add_task(Task(title, '08:00', DAY))
    assert len(s.detect_conflicts(DAY)) == 1


def test_empty_household(household):
    _, _, _, s = household
    assert s.sort_by_time() == []
    assert s.detect_conflicts() == []
    assert s.build_daily_plan(DAY, 0)['selected'] == []


def test_priority_budget_selection(household):
    _, a, b, s = household
    low = Task('Play', '07:00', DAY, duration_minutes=10, priority='low')
    high = Task('Meds', '09:00', DAY, duration_minutes=10, priority='high')
    big = Task('Vet', '08:00', DAY, duration_minutes=60, priority='high')
    a.add_task(low)
    b.add_task(high)
    b.add_task(big)
    plan = s.build_daily_plan(DAY, 20)
    assert plan['selected'] == [(a, low), (b, high)]
    assert plan['skipped'] == [(b, big)]
    assert plan['used_minutes'] == 20
    assert len(s.build_daily_plan(DAY, 0)['skipped']) == 3


@pytest.mark.parametrize('bad_time', ['8:00', '24:00', '12:60', 'noon', '08:00\n'])
def test_invalid_time(bad_time):
    with pytest.raises(ValueError):
        Task('Walk', bad_time)


@pytest.mark.parametrize('changes', [{'description': ''}, {'frequency': 'monthly'},
                                    {'priority': 'urgent'}, {'duration_minutes': 0},
                                    {'duration_minutes': 241}, {'due_date': '2026-10-18'}])
def test_invalid_task_fields(changes):
    inputs = {'description': 'Walk', 'time': '08:00'}
    inputs.update(changes)
    with pytest.raises(ValueError):
        Task(**inputs)


def test_duplicate_pet_and_missing_task(household):
    owner, _, _, s = household
    with pytest.raises(ValueError):
        owner.add_pet(Pet(' mochi ', 'dog'))
    with pytest.raises(ValueError):
        s.mark_task_complete('missing')
    with pytest.raises(ValueError):
        s.build_daily_plan(DAY, -1)
