"""Exercise the real Streamlit app through its supported AppTest harness."""
from datetime import date, timedelta
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def widget(elements, label):
    return next(element for element in elements if element.label == label)


def test_add_schedule_complete_filter_and_edit():
    app = AppTest.from_file(APP).run()
    assert not app.exception
    widget(app.text_input, 'Pet name').input('Mochi')
    widget(app.button, 'Add pet').click().run()
    assert len(app.session_state.owner.pets) == 1
    widget(app.text_input, 'Task description').input('Breakfast')
    widget(app.selectbox, 'Frequency').select('daily')
    widget(app.button, 'Add task').click().run()
    assert not app.exception
    assert app.session_state.owner.pets[0].tasks[0].description == 'Breakfast'
    widget(app.text_input, 'Edit description').input('Morning food')
    widget(app.button, 'Save changes').click().run()
    assert app.session_state.owner.pets[0].tasks[0].description == 'Morning food'
    widget(app.button, 'Mark complete').click().run()
    tasks = app.session_state.owner.pets[0].tasks
    assert tasks[0].completed
    assert tasks[1].due_date == date.today() + timedelta(days=1)
    widget(app.selectbox, 'Status').select('Pending').run()
    assert any('No tasks match' in i.value for i in app.info)
    widget(app.date_input, 'View date').set_value(date.today() + timedelta(days=1)).run()
    assert len(app.table) >= 1
    assert not app.exception


def test_conflict_warning_and_session_persistence():
    app = AppTest.from_file(APP).run()
    for pet in ['Mochi', 'Luna']:
        widget(app.text_input, 'Pet name').input(pet)
        widget(app.button, 'Add pet').click().run()
        widget(app.selectbox, 'Pet').select(pet)
        widget(app.text_input, 'Task description').input('Food')
        widget(app.button, 'Add task').click().run()
    assert any('conflict:' in warning.value for warning in app.warning)
    assert len(app.session_state.owner.pets) == 2
    widget(app.selectbox, 'Filter by pet').select('Luna').run()
    assert len(app.table[0].value) == 1
    assert not app.exception
