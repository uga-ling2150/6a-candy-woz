"""
FORM: WizardLobby — code-behind
Pair with WizardLobby.html. Touches only code_label, catalogue_repeater, poll_timer.
"""
from ._anvil_designer import WizardLobbyTemplate
from anvil import *
import anvil.server


class WizardLobby(WizardLobbyTemplate):
  def __init__(self, student_name, **properties):
    self.init_components(**properties)
    self.student_name = student_name
    self.room_code = anvil.server.call('create_room', student_name)
    self.code_label.text = self.room_code
    self.catalogue_repeater.items = anvil.server.call('get_catalogue')
    self.poll_timer.interval = 2

  def poll_timer_tick(self, **event_args):
    status = anvil.server.call('get_room_status', self.room_code)
    if status['status'] == 'active':
      self.poll_timer.interval = 0  # stop polling
      open_form(
        'ChatSession',
        room_code=self.room_code,
        role='wizard',
        student_name=self.student_name,
      )