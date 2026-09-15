"""
FORM: ChatSession
Opened with: open_form('ChatSession', room_code=code, role='wizard'|'human', student_name=name)

COMPONENTS TO ADD:
  - Label             name: dialogue_label     text: "Dialogue 1"
  - HtmlPanel/Label    name: timer_label        text: "10:00"
        Accessibility: wrap this label's underlying HTML with role="status" and
        aria-live="polite" (in Anvil: use a plain HTML template component instead of a
        Label for this one, e.g. <span role="status" aria-live="polite">{{timer_text}}</span>,
        so screen readers hear each update). A Label alone will not announce changes.
  - Button             name: extend_button      text: "+2 minutes"  role: "btn-uga-outline"
  - ColumnPanel        name: catalogue_panel     visible: only when role == 'wizard'
      - Label           name: catalogue_title     text: "Catalogue reference"
      - RepeatingPanel   name: catalogue_repeater  (same item template as WizardLobby)
  - RepeatingPanel      name: transcript_repeater  item_template: a bubble row using the
        .nlg-bubble CSS class, right-aligned + red border for 'wizard', left-aligned +
        default border for 'human'. Bind item['speaker'] to choose alignment/class.
  - TextBox             name: message_box        placeholder: "Type your message..."
  - Button              name: send_button        text: "Send"  role: "btn-uga"
  - Button              name: new_dialogue_button text: "End this dialogue, start a new one"
                         role: "btn-uga-outline"
  - Label               name: time_up_label       text: "" visible: False  (see below)
  - Button              name: go_to_annotation_button text: "Go to annotation" visible: False
  - Timer               name: poll_timer          interval: 2

Suggested time_up_label text once the clock hits zero:
  "Time's up! Head over to annotation to label the turns from your dialogues."
"""
from ._anvil_designer import ChatSessionTemplate
from anvil import *
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

    self.go_to_annotation_button.visible = False
    self.time_up_label.visible = False

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
        self.timer_label.role = 'text-primary'  # visual warning, color is not the only cue
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
    self.time_up_label.visible = True
    self.go_to_annotation_button.visible = True
    self.poll_timer.interval = 0

  def poll_timer_tick(self, **event_args):
    self._refresh()

  def send_button_click(self, **event_args):
    text = self.message_box.text.strip() if self.message_box.text else ""
    if not text:
      return
    anvil.server.call('send_turn', self.room_code, self.role, text)
    self.message_box.text = ""
    self._refresh()

  def new_dialogue_button_click(self, **event_args):
    anvil.server.call('start_new_dialogue', self.room_code)
    self.last_turn_index = 0
    self.transcript_repeater.items = []
    self._refresh()

  def extend_button_click(self, **event_args):
    anvil.server.call('extend_session', self.room_code)
    self._refresh()

  def go_to_annotation_button_click(self, **event_args):
    open_form(
      'AnnotationForm',
      room_code=self.room_code,
      student_name=self.student_name,
    )
