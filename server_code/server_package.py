"""
Server Module: server_rooms
Handles room creation/joining, the 10-minute session clock, sending/polling
chat turns, and switching between dialogues within one session.
"""
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.tz
import random
import datetime

SESSION_MINUTES = 10
EXTENSION_MINUTES = 2

# Light friction, not real auth — change this before class. Keeps students from
# wandering into the instructor dashboard by accident, nothing more than that.
INSTRUCTOR_PASSCODE = "dawgs2026"


@anvil.server.callable
def check_instructor_code(code):
  return code == INSTRUCTOR_PASSCODE


def _make_room_code():
  return "CANDY-{:04d}".format(random.randint(1000, 9999))


@anvil.server.callable
def create_room(wizard_name):
  """Wizard calls this to open a new room. Returns the room code."""
  if not wizard_name or not wizard_name.strip():
    raise anvil.server.PermissionDenied("Please enter your name first.")

  code = _make_room_code()
  # Ensure the code isn't already in use by a live room
  while app_tables.rooms.get(room_code=code, status=q.any_of("waiting", "active")):
    code = _make_room_code()

  app_tables.rooms.add_row(
    room_code=code,
    wizard_name=wizard_name.strip(),
    human_name=None,
    status="waiting",
    dialogue_count=1,
    session_start=None,
    session_end_deadline=None,
    created_on=datetime.datetime.now(anvil.tz.UTC),
  )
  return code


@anvil.server.callable
def join_room(room_code, human_name):
  """Human calls this with the code the Wizard shared. Returns an explicit
  result dict since a bad/expired code is an expected, user-fixable case
  the client displays inline."""
  if not room_code or not human_name or not human_name.strip():
    return {"ok": False, "message": "Enter both the room code and your name."}

  room = app_tables.rooms.get(room_code=room_code.strip().upper())
  if not room:
    return {"ok": False, "message": "That room code wasn't found. Double check it with your partner."}
  if room["status"] == "ended":
    return {"ok": False, "message": "That room's session already ended."}
  if room["status"] == "active" and room["human_name"] and room["human_name"] != human_name.strip():
    return {"ok": False, "message": "That room already has a partner."}

  now = datetime.datetime.now(anvil.tz.UTC)
  room.update(
    human_name=human_name.strip(),
    status="active",
    session_start=now,
    session_end_deadline=now + datetime.timedelta(minutes=SESSION_MINUTES),
  )
  return {"ok": True, "room_code": room["room_code"], "wizard_name": room["wizard_name"]}


@anvil.server.callable
def get_room_status(room_code):
  """Used by both lobbies and ChatSession to poll room state and remaining time."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room:
    raise anvil.server.PermissionDenied("Room not found.")

  seconds_left = None
  if room["session_end_deadline"]:
    seconds_left = (room["session_end_deadline"] - datetime.datetime.now()).total_seconds()

  return {
    "status": room["status"],
    "wizard_name": room["wizard_name"],
    "human_name": room["human_name"],
    "dialogue_count": room["dialogue_count"],
    "seconds_left": seconds_left,
  }


@anvil.server.callable
def extend_session(room_code):
  """Either student can add time back if they need an accommodation."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room or not room["session_end_deadline"]:
    raise anvil.server.PermissionDenied("Room not found or not active.")
  room.update(session_end_deadline=room["session_end_deadline"] + datetime.timedelta(minutes=EXTENSION_MINUTES))
  return True


@anvil.server.callable
def send_turn(room_code, speaker, message_text):
  """Log one chat turn (speaker is 'wizard' or 'human')."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room or room["status"] != "active":
    raise anvil.server.PermissionDenied("This session isn't active.")
  if not message_text or not message_text.strip():
    return

  existing = app_tables.turns.search(
    room=room, dialogue_number=room["dialogue_count"]
  )
  next_index = len(list(existing)) + 1

  app_tables.turns.add_row(
    room=room,
    dialogue_number=room["dialogue_count"],
    turn_index=next_index,
    speaker=speaker,
    message_text=message_text.strip(),
    timestamp=datetime.datetime.now(),
    intent_label=None,
    annotator_name=None,
  )


@anvil.server.callable
def get_turns(room_code, since_index=0):
  """Poll for all turns in the CURRENT dialogue, optionally only new ones."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room:
    raise anvil.server.PermissionDenied("Room not found.")

  rows = app_tables.turns.search(
    tables.order_by("turn_index"),
    room=room,
    dialogue_number=room["dialogue_count"],
  )
  turns = [
    {
      "speaker": r["speaker"],
      "message_text": r["message_text"],
      "turn_index": r["turn_index"],
    }
    for r in rows
    if r["turn_index"] > since_index
  ]
  return {"dialogue_number": room["dialogue_count"], "turns": turns}


@anvil.server.callable
def start_new_dialogue(room_code):
  """Either student can end the current dialogue and start a fresh one."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room or room["status"] != "active":
    raise anvil.server.PermissionDenied("This session isn't active.")
  room.update(dialogue_count=room["dialogue_count"] + 1)
  return room["dialogue_count"]


@anvil.server.callable
def end_session(room_code):
  room = app_tables.rooms.get(room_code=room_code)
  if room:
    room.update(status="ended")