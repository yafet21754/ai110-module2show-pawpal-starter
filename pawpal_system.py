"""PawPal+ backend, independent of Streamlit."""
from dataclasses import dataclass, field
from datetime import date

@dataclass
class Task:
    description: str
    time: str
    due_date: date = field(default_factory=date.today)
    frequency: str = 'once'
    completed: bool = False

    def mark_complete(self):
        """Mark this occurrence complete."""
        raise NotImplementedError

@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task):
        """Attach a care task to this pet."""
        raise NotImplementedError

@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet):
        """Register a pet."""
        raise NotImplementedError

    def get_all_tasks(self):
        """Return tasks across all pets."""
        raise NotImplementedError

class Scheduler:
    def __init__(self, owner):
        self.owner = owner

    def sort_by_time(self):
        """Return tasks in chronological order."""
        raise NotImplementedError
