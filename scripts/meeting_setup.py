from Wizard_of_Oz_and_dialogue_annotation import server_package as app
from Wizard_of_Oz_and_dialogue_annotation.server_seed import seed_meeting_data
from anvil.tables import app_tables
from datetime import datetime, timedelta
import anvil.tz
print('Idempotent seed:', seed_meeting_data())
code = 'CANDY-4807'
room = app_tables.rooms.get(room_code=code)
assert room['wizard_name'] == 'QA Wizard Sep16'
assert 'human_persona' not in app.get_room_status(code)
old_deadline = room['session_end_deadline']
old_persona = room['human_persona']
result = app.join_room(code, 'QA Human Sep16')
assert result['human_persona'] == old_persona
assert room['session_end_deadline'] == old_deadline
try:
  app.send_turn(code, 'human', 'x' * 1001)
  raise AssertionError('Too-long message accepted')
except ValueError:
  print('PASS: server rejects >1000 characters')
print('PASS: stable persona, no persona in shared status, rejoin preserves timer')
room.update(session_end_deadline=datetime.now(anvil.tz.tzutc()) - timedelta(seconds=1))
print('Only QA room expired for annotation and extension test')
