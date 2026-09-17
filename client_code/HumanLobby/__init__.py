"""
FORM: HumanLobby — code-behind
Opened with: open_form('HumanLobby', student_name=name)
Pair with HumanLobby.html. Touches: code_box, error_label, join_button.
"""
from ._anvil_designer import HumanLobbyTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class HumanLobby(HumanLobbyTemplate):
  def __init__(self, student_name, **properties):
    self.init_components(**properties)
    self.student_name = student_name

  @handle("join_button", "click")
  def join_button_click(self, **event_args):
    self.error_label.visible = False
    code = self.code_box.text.strip() if self.code_box.text else ""
    if not code:
      self.error_label.text = "Enter the room code your partner gave you."
      self.error_label.visible = True
      return
    result = anvil.server.call('join_room', code, self.student_name)
    if not result['ok']:
      self.error_label.text = result['message']
      self.error_label.visible = True
      return

    open_form(
      'ChatSession',
      room_code=result['room_code'],
      role='human',
      human_persona=result.get('human_persona'),
      student_name=self.student_name,
    )
