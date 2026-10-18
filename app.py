"""Streamlit presentation layer for PawPal+."""
from datetime import date, time
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title='PawPal+', page_icon='🐾', layout='wide')
st.title('🐾 PawPal+')
st.caption('A little planning. A happier pet. Keep care routines together across all your pets.')
if 'owner' not in st.session_state:
    st.session_state.owner = Owner('Jordan')
owner = st.session_state.owner
scheduler = Scheduler(owner)

with st.sidebar:
    st.header('Your household')
    with st.form('owner_form'):
        owner_name = st.text_input('Owner name', value=owner.name)
        if st.form_submit_button('Save owner'):
            if owner_name.strip():
                owner.name = owner_name.strip()
                st.success('Owner saved.')
            else:
                st.error('Owner name is required.')
    st.caption('Data stays during this browser session. A new session or server restart starts fresh.')
    st.subheader('Add a pet')
    with st.form('pet_form', clear_on_submit=True):
        pet_name = st.text_input('Pet name')
        species = st.selectbox('Species', ['dog', 'cat', 'other'])
        if st.form_submit_button('Add pet'):
            try:
                owner.add_pet(Pet(pet_name, species))
                st.success('Pet added.')
            except ValueError as exc:
                st.error(str(exc))

st.subheader(f"{owner.name}'s care dashboard")
if not owner.pets:
    st.info('Start by adding a pet in the sidebar, then schedule its first care task.')
else:
    with st.expander('Schedule a task', expanded=True):
        with st.form('task_form', clear_on_submit=True):
            pet_choice = st.selectbox('Pet', [p.name for p in owner.pets])
            description = st.text_input('Task description')
            c1, c2, c3 = st.columns(3)
            due = c1.date_input('Due date', value=date.today())
            at_time = c2.time_input('Time', value=time(8, 0))
            frequency = c3.selectbox('Frequency', ['once', 'daily', 'weekly'])
            c4, c5 = st.columns(2)
            duration = c4.number_input('Duration (minutes)', min_value=1, max_value=240, value=15)
            priority = c5.selectbox('Priority', ['high', 'medium', 'low'], index=1)
            if st.form_submit_button('Add task'):
                try:
                    task = Task(description, at_time.strftime('%H:%M'), due, frequency, int(duration), priority)
                    next(p for p in owner.pets if p.name == pet_choice).add_task(task)
                    st.success('Task scheduled.')
                except ValueError as exc:
                    st.error(str(exc))

    c1, c2, c3 = st.columns(3)
    view_date = c1.date_input('View date', value=date.today())
    pet_filter = c2.selectbox('Filter by pet', ['All pets'] + [p.name for p in owner.pets])
    status = c3.selectbox('Status', ['All', 'Pending', 'Completed'])
    pet_arg = None if pet_filter == 'All pets' else pet_filter
    completed_arg = {'All': None, 'Pending': False, 'Completed': True}[status]
    rows = scheduler.sort_by_time(pet_arg, completed_arg, view_date)
    st.subheader('Daily schedule')
    st.caption('Warnings cover the whole household on this date, even when the table is filtered.')
    for warning in scheduler.detect_conflicts(view_date):
        st.warning(warning)
    if rows:
        st.table([{'Time': t.time, 'Pet': p.name, 'Care task': t.description,
                   'Minutes': t.duration_minutes, 'Priority': t.priority.title(),
                   'Repeats': t.frequency, 'Status': 'Complete' if t.completed else 'Pending'}
                  for p, t in rows])
    else:
        st.info('No tasks match these filters.')
    pending = [(p, t) for p, t in rows if not t.completed]
    if pending:
        by_id = {t.task_id: (p, t) for p, t in pending}
        selected_id = st.selectbox('Task to complete', list(by_id),
                                   format_func=lambda i: f'{by_id[i][1].time} · {by_id[i][0].name} · {by_id[i][1].description}')
        if st.button('Mark complete'):
            following = scheduler.mark_task_complete(selected_id)
            st.session_state.notice = ('Completed. Next occurrence: ' + str(following.due_date)
                                       if following else 'Task completed.')
            st.rerun()
    if 'notice' in st.session_state:
        st.success(st.session_state.pop('notice'))

    with st.expander('Edit a pending task'):
        editable = {t.task_id: (p, t) for p, t in scheduler.sort_by_time(completed=False)}
        if editable:
            edit_id = st.selectbox('Task to edit', list(editable),
                                  format_func=lambda i: f'{editable[i][0].name} · {editable[i][1].due_date} · {editable[i][1].description}')
            edit_pet, edit_task = editable[edit_id]
            with st.form('edit_' + edit_id):
                new_description = st.text_input('Edit description', value=edit_task.description)
                new_date = st.date_input('Edit date', value=edit_task.due_date)
                new_time = st.time_input('Edit time', value=edit_task.scheduled_at.time())
                new_duration = st.number_input('Edit duration', min_value=1, max_value=240, value=edit_task.duration_minutes)
                new_priority = st.selectbox('Edit priority', ['high', 'medium', 'low'],
                                            index=['high', 'medium', 'low'].index(edit_task.priority))
                new_frequency = st.selectbox('Edit frequency', ['once', 'daily', 'weekly'],
                                             index=['once', 'daily', 'weekly'].index(edit_task.frequency))
                if st.form_submit_button('Save changes'):
                    try:
                        validated = Task(new_description, new_time.strftime('%H:%M'), new_date,
                                         new_frequency, int(new_duration), new_priority)
                        validated.task_id = edit_task.task_id
                        edit_pet.tasks[edit_pet.tasks.index(edit_task)] = validated
                        st.session_state.notice = 'Task updated.'
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        else:
            st.info('There are no pending tasks to edit.')

    st.subheader('Plan within your available care time')
    budget = st.number_input('Available minutes for this date', min_value=0, max_value=1440, value=60)
    plan = scheduler.build_daily_plan(view_date, int(budget))
    st.caption(plan['explanation'])
    st.write(f"Selected {len(plan['selected'])} tasks · {plan['used_minutes']} of {int(budget)} minutes")
    if plan['selected']:
        st.table([{'Time': t.time, 'Pet': p.name, 'Task': t.description,
                   'Why selected': f'{t.priority.title()} priority; fits remaining budget'}
                  for p, t in plan['selected']])
    if plan['skipped']:
        st.warning('Outside the time budget: ' + ', '.join(f'{p.name}: {t.description}' for p, t in plan['skipped']))
    st.caption('This plan uses every pet on the selected date. It does not move start times or resolve overlapping durations.')
