"""Pet care entities and scheduling algorithms; no UI dependencies."""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import re
from uuid import uuid4


def _required(value: str, label: str) -> str:
    """Return trimmed nonempty text or reject the input."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} is required.')
    return value.strip()


@dataclass
class Task:
    description: str
    time: str
    due_date: date = field(default_factory=date.today)
    frequency: str = 'once'
    duration_minutes: int = 15
    priority: str = 'medium'
    completed: bool = False
    task_id: str = field(default_factory=lambda: uuid4().hex, init=False)

    def __post_init__(self):
        """Validate task inputs and normalize text."""
        self.description = _required(self.description, 'Description')
        if not isinstance(self.time, str) or not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', self.time):
            raise ValueError('Time must use 24-hour HH:MM format.')
        if type(self.due_date) is not date:
            raise ValueError('Due date must be a date.')
        if self.frequency not in {'once', 'daily', 'weekly'}:
            raise ValueError('Frequency must be once, daily, or weekly.')
        if self.priority not in {'low', 'medium', 'high'}:
            raise ValueError('Priority must be low, medium, or high.')
        if type(self.duration_minutes) is not int or not 1 <= self.duration_minutes <= 240:
            raise ValueError('Duration must be between 1 and 240 minutes.')

    @property
    def scheduled_at(self) -> datetime:
        """Combine the date and time for chronological comparisons."""
        return datetime.combine(self.due_date, datetime.strptime(self.time, '%H:%M').time())

    def mark_complete(self) -> None:
        """Mark this occurrence complete; use Scheduler to create recurrence."""
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self):
        """Normalize pet details."""
        self.name = _required(self.name, 'Pet name')
        self.species = _required(self.species, 'Species')

    def add_task(self, task: Task) -> None:
        """Add a distinct task occurrence to this pet."""
        if any(t.task_id == task.task_id for t in self.tasks):
            raise ValueError('This task is already attached to the pet.')
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self):
        """Require an owner name."""
        self.name = _required(self.name, 'Owner name')

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with a unique case-insensitive name."""
        if any(p.name.casefold() == pet.name.casefold() for p in self.pets):
            raise ValueError('A pet with that name already exists.')
        if any(t.task_id == old.task_id for t in pet.tasks for _, old in self.get_all_tasks()):
            raise ValueError('A task cannot belong to more than one pet.')
        self.pets.append(pet)

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return pet/task pairs from every pet, retaining ownership."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    def __init__(self, owner: Owner):
        """Keep one owner as the source of all scheduling data."""
        self.owner = owner

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None,
                     due_date: date | None = None) -> list[tuple[Pet, Task]]:
        """Filter across all pets by optional pet, status, and exact date."""
        return [(pet, task) for pet, task in self.owner.get_all_tasks()
                if (pet_name is None or pet.name.casefold() == pet_name.casefold())
                and (completed is None or task.completed == completed)
                and (due_date is None or task.due_date == due_date)]

    def sort_by_time(self, pet_name: str | None = None, completed: bool | None = None,
                     due_date: date | None = None) -> list[tuple[Pet, Task]]:
        """Return a new chronological list without mutating stored tasks."""
        return sorted(self.filter_tasks(pet_name, completed, due_date),
                      key=lambda pair: pair[1].scheduled_at)

    def mark_task_complete(self, task_id: str) -> Task | None:
        """Complete once and append the next daily or weekly occurrence."""
        for pet, task in self.owner.get_all_tasks():
            if task.task_id == task_id:
                if task.completed:
                    return None
                task.mark_complete()
                if task.frequency == 'once':
                    return None
                days = 1 if task.frequency == 'daily' else 7
                following = Task(task.description, task.time,
                                 task.due_date + timedelta(days=days), task.frequency,
                                 task.duration_minutes, task.priority)
                pet.add_task(following)
                return following
        raise ValueError('Task was not found.')

    def detect_conflicts(self, due_date: date | None = None) -> list[str]:
        """Warn about pending tasks sharing an exact date and start time."""
        groups: dict[datetime, list[str]] = {}
        for pet, task in self.filter_tasks(completed=False, due_date=due_date):
            groups.setdefault(task.scheduled_at, []).append(f'{pet.name}: {task.description}')
        return [f'{when:%Y-%m-%d %H:%M} conflict: ' + ' / '.join(groups[when])
                for when in sorted(groups) if len(groups[when]) > 1]

    def build_daily_plan(self, due_date: date, available_minutes: int) -> dict:
        """Greedily select pending tasks by priority within a total care budget."""
        if type(available_minutes) is not int or available_minutes < 0:
            raise ValueError('Available minutes must be a nonnegative integer.')
        rank = {'high': 0, 'medium': 1, 'low': 2}
        candidates = sorted(self.filter_tasks(completed=False, due_date=due_date),
                            key=lambda pair: (rank[pair[1].priority], pair[1].scheduled_at))
        selected, skipped, used = [], [], 0
        for pet, task in candidates:
            if used + task.duration_minutes <= available_minutes:
                selected.append((pet, task))
                used += task.duration_minutes
            else:
                skipped.append((pet, task))
        selected.sort(key=lambda pair: pair[1].scheduled_at)
        return {'selected': selected, 'skipped': skipped, 'used_minutes': used,
                'explanation': 'High priority first, then medium and low; earlier times break ties. '
                'Tasks that fit the remaining care budget are selected, then displayed by time. '
                'Start times stay fixed; check conflict warnings separately.'}
