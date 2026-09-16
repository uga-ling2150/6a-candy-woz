"""
FORM: HumanLobby
Opened with: open_form('HumanLobby', student_name=name)

COMPONENTS TO ADD:
  - Label            name: title_label        text: "Join your partner's store"
  - Label            name: instructions_label  text: (see below)
  - Label            name: code_label          text: "Room code"
  - TextBox          name: code_box            placeholder: "CANDY-XXXX"
  - Label            name: error_label         text: ""  visible: False  foreground: var(--uga-red)
  - Button           name: join_button         text: "Join"  role: "btn-uga"

Suggested instructions text:
  "Your partner is running a candy store counter and has a room code for you. Type it in
   below to join — you'll be playing the customer, so just imagine you're stopping by to
   pick up some candy."
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

  def join_button_click(self, **event_args):
    self.error_label.visible = False
    code = self.code_box.text.strip() if self.code_box.text else ""
    if not code:
      self.error_label.text = "Enter the room code your partner gave you."
      self.error_label.visible = True
      return
    try:
      result = anvil.server.call('join_room', code, self.student_name)
    except anvil.server.PermissionDenied as e:
      self.error_label.text = str(e)
      self.error_label.visible = True
      return

    open_form(
      'ChatSession',
      room_code=result['room_code'],
      role='human',
      student_name=self.student_name,
    )
