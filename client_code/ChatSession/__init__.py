"""
FORM: ChatSession — code-behind
Pair with ChatSession.html. Touches: dialogue_label, timer_label, extend_button,
catalogue_panel, catalogue_repeater, transcript_repeater, message_box,
send_button, new_dialogue_button, time_up_panel, time_up_label,
go_to_annotation_button, poll_timer.
"""
from ._anvil_designer import ChatSessionTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


class ChatSession(ChatSessionTemplate):
  def __init__(self, room_code, role, student_name, **properties):
    self.init_components(**properties)
    self.room_code = room_code
    self.role = role
    self.student_name = student_name
    self.last_turn_index = 0
    self.time_up = False

    self.catalogue_panel.visible = (role == 'wizard')
    if role == 'wizard':
      self.catalogue_repeater.items = anvil.server.call('get_catalogue')

    self.time_up_panel.visible = False
    self.message_box.set_event_handler('pressed_enter', self.send_button_click)

    self.poll_timer.interval = 2
    self._refresh()  # initial paint so students aren't staring at a blank screen

  def _format_seconds(self, seconds):
    seconds = max(0, int(seconds))
    return "{:d}:{:02d}".format(seconds // 60, seconds % 60)

  def _refresh(self):
    status = anvil.server.call('get_room_status', self.room_code)
    self.dialogue_label.text = "Dialogue {}".format(status['dialogue_count'])

    seconds_left = status['seconds_left']
    if seconds_left is not None:
      self.timer_label.text = self._format_seconds(seconds_left)
      if seconds_left <= 60 and not self.time_up:
        self.timer_label.role = 'text-primary'  # visual warning, not the only cue
      if seconds_left <= 0 and not self.time_up:
        self._handle_time_up()

    result = anvil.server.call('get_turns', self.room_code, self.last_turn_index)
    if result['turns']:
      self.transcript_repeater.items = (self.transcript_repeater.items or []) + result['turns']
      self.last_turn_index = result['turns'][-1]['turn_index']

  def _handle_time_up(self):
    self.time_up = True
    self.message_box.enabled = False
    self.send_button.enabled = False
    self.new_dialogue_button.enabled = False
    self.time_up_panel.visible = True
    self.poll_timer.interval = 0

  @handle("poll_timer", "tick")
  def poll_timer_tick(self, **event_args):
    self._refresh()

  @handle("send_button", "click")
  def send_button_click(self, **event_args):
    text = self.message_box.text.strip() if self.message_box.text else ""
    if not text:
      return
    anvil.server.call('send_turn', self.room_code, self.role, text)
    self.message_box.text = ""
    self._refresh()

  @handle("new_dialogue_button", "click")
  def new_dialogue_button_click(self, **event_args):
    anvil.server.call('start_new_dialogue', self.room_code)
    self.last_turn_index = 0
    self.transcript_repeater.items = []
    self._refresh()

  @handle("extend_button", "click")
  def extend_button_click(self, **event_args):
    anvil.server.call('extend_session', self.room_code)
    self._refresh()

  @handle("go_to_annotation_button", "click")
  def go_to_annotation_button_click(self, **event_args):
    open_form(
      'AnnotationForm',
      room_code=self.room_code,
      student_name=self.student_name,
    )