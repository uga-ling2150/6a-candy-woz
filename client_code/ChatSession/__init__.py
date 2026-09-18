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
import anvil.js


class ChatSession(ChatSessionTemplate):
  def __init__(self, room_code, role, student_name, human_persona=None, **properties):
    self.init_components(**properties)
    dialogue_heading = anvil.js.get_dom_node(self.dialogue_label)
    dialogue_heading.setAttribute("role", "heading")
    dialogue_heading.setAttribute("aria-level", "2")
    root = anvil.js.get_dom_node(self)
    self.activity_nodes = {name: root.querySelector("#woz-" + name.replace("_", "-")) for name in ["persona_title", "persona_text", "persona_panel", "persona_hint", "message_count", "message_error"]}
    self.room_code = room_code
    self.role = role
    self.student_name = student_name
    self.last_turn_index = 0
    self.time_up = False
    self._refreshing = False
    self._sending = False
    self.current_dialogue = None

    if role == "human":
      self._update_persona_display(human_persona)

    self.catalogue_panel.visible = (role == 'wizard')
    if role == 'wizard':
      self.catalogue_repeater.items = anvil.server.call('get_catalogue')

    self.time_up_panel.visible = False
    self.message_box.set_event_handler('pressed_enter', self.send_button_click)
    message_input = anvil.js.get_dom_node(self.message_box)
    if message_input.tagName.lower() != 'input':
      message_input = message_input.querySelector('input')
    message_input.setAttribute('maxlength', '1000')
    message_input.setAttribute('aria-label', 'Your message')
    message_input.setAttribute('aria-describedby', 'woz-message-help woz-message-count')
    message_input.addEventListener('input', self.message_changed)
    self.message_changed()

    self.poll_timer.interval = 2
    self._refresh()  # initial paint so students aren't staring at a blank screen

  def _update_persona_display(self, human_persona):
    persona_code = human_persona.get("persona_code") if human_persona else None
    if persona_code:
      self.activity_nodes["persona_title"].textContent = human_persona.get("title", "Your customer role")
      self.activity_nodes["persona_text"].textContent = human_persona.get("prompt", "")
      self.activity_nodes["persona_hint"].hidden = False
    else:
      self.activity_nodes["persona_title"].textContent = "No customer role assigned"
      self.activity_nodes["persona_text"].textContent = (
        "Now you can act freely, and order anything you want! "
        "You are no longer assigned a user persona."
      )
      self.activity_nodes["persona_hint"].hidden = True
    self.activity_nodes["persona_panel"].hidden = False

  def _format_seconds(self, seconds):
    seconds = max(0, int(seconds))
    return "{:d}:{:02d}".format(seconds // 60, seconds % 60)

  def _refresh(self):
    # send_button_click and poll_timer can both call this; anvil.server.call
    # yields to the browser event loop, so an overlapping call would race on
    # self.last_turn_index and append the same turn twice.
    if self._refreshing:
      return
    self._refreshing = True
    try:
      status = anvil.server.call_s('get_room_status', self.room_code)
      if self.current_dialogue != status['dialogue_count']:
        self.current_dialogue = status['dialogue_count']
        self.last_turn_index = 0
        self.transcript_repeater.items = []
        if self.role == "human":
          self._update_persona_display(status['human_persona'])
      self.dialogue_label.text = "Dialogue {}".format(status['dialogue_count'])

      seconds_left = status['seconds_left']
      if seconds_left is not None:
        self.timer_label.text = self._format_seconds(seconds_left)
        if seconds_left > 0 and self.time_up:
          self.time_up = False
          self.message_box.enabled = True
          self.send_button.enabled = True
          self.new_dialogue_button.enabled = True
          self.time_up_panel.visible = False
        if seconds_left > 60:
          self.timer_label.role = None
        if seconds_left <= 60 and not self.time_up:
          self.timer_label.role = 'text-primary'  # visual warning, not the only cue
        if seconds_left <= 0 and not self.time_up:
          self._handle_time_up()

      result = anvil.server.call_s('get_turns', self.room_code, self.last_turn_index)
      if result['turns']:
        self.transcript_repeater.items = (self.transcript_repeater.items or []) + result['turns']
        self.last_turn_index = result['turns'][-1]['turn_index']
    finally:
      self._refreshing = False

  def _handle_time_up(self):
    self.time_up = True
    self.message_box.enabled = False
    self.send_button.enabled = False
    self.new_dialogue_button.enabled = False
    self.time_up_panel.visible = True
    self.poll_timer.interval = 2

  @handle("poll_timer", "tick")
  def poll_timer_tick(self, **event_args):
    self._refresh()

  def message_changed(self, *args, **event_args):
    length = len(self.message_box.text or "")
    self.activity_nodes['message_count'].textContent = "{} / 1,000 characters".format(length)
    self.activity_nodes['message_error'].hidden = True

  @handle("send_button", "click")
  def send_button_click(self, **event_args):
    if self._sending or self.time_up:
      return
    raw_text = self.message_box.text or ""
    text = raw_text.strip()
    if not text:
      return
    if len(raw_text) > 1000:
      self.activity_nodes['message_error'].textContent = "Please keep each message to 1,000 characters or fewer."
      self.activity_nodes['message_error'].hidden = False
      return
    self._sending = True
    self.send_button.enabled = False
    try:
      anvil.server.call('send_turn', self.room_code, self.role, raw_text)
      self.message_box.text = ""
      self.message_changed()
      self._refresh()
    except Exception:
      self.activity_nodes['message_error'].textContent = "Your message was not sent. Please check the connection and try again."
      self.activity_nodes['message_error'].hidden = False
    finally:
      self._sending = False
      self.send_button.enabled = not self.time_up

  @handle("new_dialogue_button", "click")
  def new_dialogue_button_click(self, **event_args):
    if self.time_up:
      return
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