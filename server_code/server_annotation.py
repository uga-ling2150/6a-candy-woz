"""
Server Module: server_annotation
Serves reference data (catalogue, intent taxonomy) and handles saving/reading
student annotations of their own dialogue turns.
"""
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


@anvil.server.callable
def get_catalogue():
  """Wizard-only reference panel. Returns every catalogue item."""
  rows = app_tables.catalogue_items.search(tables.order_by("category"))
  return [
    {
      "item_name": r["item_name"],
      "category": r["category"],
      "price": r["price"],
      "flavor_notes": r["flavor_notes"],
      "in_stock": r["in_stock"],
    }
    for r in rows
  ]


@anvil.server.callable
def get_intent_labels():
  """The fixed taxonomy shown as dropdown options during annotation."""
  rows = app_tables.intent_labels.search(tables.order_by("label_name"))
  return [
    {
      "label_code": r["label_code"],
      "label_name": r["label_name"],
      "description": r["description"],
      "example_phrase": r["example_phrase"],
    }
    for r in rows
  ]


@anvil.server.callable
def get_turns_for_annotation(room_code):
  """All turns across all dialogues in a room, for the annotation screen."""
  room = app_tables.rooms.get(room_code=room_code)
  if not room:
    raise anvil.server.PermissionDenied("Room not found.")

  rows = app_tables.turns.search(
    tables.order_by("dialogue_number"),
    tables.order_by("turn_index"),
    room=room,
  )
  return [
    {
      "id": r.get_id(),
      "dialogue_number": r["dialogue_number"],
      "turn_index": r["turn_index"],
      "speaker": r["speaker"],
      "message_text": r["message_text"],
      "intent_label": r["intent_label"],
    }
    for r in rows
  ]


@anvil.server.callable
def save_annotation(turn_row_id, intent_label, annotator_name):
  """Save one turn's intent label. turn_row_id comes from row.get_id()."""
  row = app_tables.turns.get_by_id(turn_row_id)
  if not row:
    raise anvil.server.PermissionDenied("Turn not found.")
  row.update(intent_label=intent_label, annotator_name=annotator_name)
  return True