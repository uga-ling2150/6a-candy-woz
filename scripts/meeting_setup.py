from anvil.tables import app_tables
from datetime import datetime, timedelta
import anvil.tz
room = app_tables.rooms.get(room_code='CANDY-7413')
assert room['wizard_name'] == 'QA Wizard axe Sep17'
room.update(session_end_deadline=datetime.now(anvil.tz.tzutc()) - timedelta(seconds=1))
print('Only QA room CANDY-7413 expired for accessibility checks')
