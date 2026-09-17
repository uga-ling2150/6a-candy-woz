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
MAX_MESSAGE_LENGTH = 1000

# Light friction, not real auth — change this before class. Keeps students from
# wandering into the instructor dashboard by accident, nothing more than that.
INSTRUCTOR_PASSCODE = "dawgs2026"


@anvil.server.callable
def check_instructor_code(code):
  return code == INSTRUCTOR_PASSCODE


def _make_room_code():
  return "CANDY-{:04d}".format(random.randint(1000, 9999))


def _persona_history(human_persona):
  """Persona codes already shown to this human in the current room so far,
  oldest first. Reads the explicit history list when present (even if it's
  empty, e.g. once every persona has already been used) and only falls back
  to the single persona_code for rooms assigned before history tracking
  existed."""
  if not human_persona:
    return []
  if "history" in human_persona:
    return human_persona["history"]
  code = human_persona.get("persona_code")
  return [code] if code else []


def _assign_persona(human_name, prior_history):
  """Give this human a customer role they haven't had yet — not in an
  earlier dialogue of this room (prior_history) and not in an earlier room.
  Once every persona has already been used by this name, keep returning a
  role-less result (never bare None) so the exhausted history is preserved
  and later dialogues stay free-form instead of looping back through the
  same personas."""
  personas = list(app_tables.user_personas.search())
  used_codes = set(prior_history)
  for row in app_tables.rooms.search(human_name=human_name):
    used_codes.update(_persona_history(row["human_persona"]))
  unused = [p for p in personas if p["persona_code"] not in used_codes]
  if not unused:
    return {"persona_code": None, "title": None, "prompt": None, "history": prior_history}
  chosen = random.choice(unused)
  return {
    "persona_code": chosen["persona_code"],
    "title": chosen["title"],
    "prompt": chosen["prompt"],
    "history": prior_history + [chosen["persona_code"]],
  }


@anvil.server.callable
def create_room(wizard_name):
  """Wizard calls this to open a new room. Returns the room code."""
  if not wizard_name or not wizard_name.strip():
    raise anvil.server.PermissionDenied("Please enter your name first.")

  if not list(app_tables.user_personas.search()):
    raise ValueError("Customer roles are not ready yet. Please ask your instructor.")

  code = _make_room_code()
  # Ensure the code isn't already in use by a live room
  while app_tables.rooms.get(room_code=code, status=q.any_of("waiting", "active")):
    code = _make_room_code()

  app_tables.rooms.add_row(
    room_code=code,
    wizard_name=wizard_name.strip(),
    human_persona=None,
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

  human_name = human_name.strip()
  if room["human_persona"] is None:
    room.update(human_persona=_assign_persona(human_name, []))

  now = datetime.datetime.now(anvil.tz.UTC)
  room.update(
    human_name=human_name,
    status="active",
    session_start=room["session_start"] or now,
    session_end_deadline=room["session_end_deadline"] or (now + datetime.timedelta(minutes=SESSION_MINUTES)),
  )
  return {"ok": True, "room_code": room["room_code"], "wizard_name": room["wizard_name"],
          "human_persona": room["human_persona"]}


@anvil.server.callable
def get_room_status(room_code):
  """Used by both lobbies and ChatSession to poll room state and remaining time."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room:
    raise anvil.server.PermissionDenied("Room not found.")

  seconds_left = None
  if room["session_end_deadline"]:
    seconds_left = (room["session_end_deadline"] - datetime.datetime.now(anvil.tz.UTC)).total_seconds()

  return {
    "status": room["status"],
    "wizard_name": room["wizard_name"],
    "human_name": room["human_name"],
    "dialogue_count": room["dialogue_count"],
    "seconds_left": seconds_left,
    "human_persona": room["human_persona"],
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
  if speaker not in ("human", "wizard"):
    raise ValueError("Unknown speaker.")
  if not isinstance(message_text, str):
    raise ValueError("Please enter a text message.")
  if len(message_text) > MAX_MESSAGE_LENGTH:
    raise ValueError("Please keep each message to 1,000 characters or fewer.")
  if not message_text.strip():
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
    timestamp=datetime.datetime.now(anvil.tz.UTC),
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
  """Either student can end the current dialogue and start a fresh one. The
  human gets a new customer role for the new dialogue, distinct from every
  role they've already had in this room or an earlier one."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room or room["status"] != "active":
    raise anvil.server.PermissionDenied("This session isn't active.")
  if room["session_end_deadline"] and datetime.datetime.now(anvil.tz.UTC) >= room["session_end_deadline"]:
    raise anvil.server.PermissionDenied("Time's up for this session.")
  new_persona = _assign_persona(room["human_name"], _persona_history(room["human_persona"]))
  room.update(dialogue_count=room["dialogue_count"] + 1, human_persona=new_persona)
  return room["dialogue_count"]


@anvil.server.callable
def end_session(room_code):
  room = app_tables.rooms.get(room_code=room_code)
  if room:
    room.update(status="ended")


@anvil.server.callable
def clear_all_training_data():
  """Instructor-only reset between classes. Refuses while any room is still
  waiting for a partner or actively in session, since wiping rooms/turns out
  from under a live chat would break it."""
  open_rooms = app_tables.rooms.search(status=q.any_of("waiting", "active"))
  if list(open_rooms):
    return {
      "ok": False,
      "message": "Can't clear yet — there's still an open chat session. "
      "Ask everyone to finish or end their session first.",
    }

  turns_cleared = 0
  for row in app_tables.turns.search():
    row.delete()
    turns_cleared += 1

  rooms_cleared = 0
  for row in app_tables.rooms.search():
    row.delete()
    rooms_cleared += 1

  return {"ok": True, "rooms_cleared": rooms_cleared, "turns_cleared": turns_cleared}