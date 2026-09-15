"""
FORM: AnnotationForm
Opened with: open_form('AnnotationForm', room_code=code, student_name=name)
  
COMPONENTS TO ADD:
  - Label              name: title_label        text: "Label your conversation"
  - Label              name: instructions_label  text: (see below)
  - Label              name: progress_label      text: "0 / 0 turns labeled"
  - RepeatingPanel      name: turns_repeater      item_template: "AnnotationRowTemplate" —
        a small form/row with:
          - Label       showing "{dialogue_number} · {speaker}: {message_text}"
          - Label       "What was this turn trying to do?"
          - DropDown    bound to intent options (label_name shown, label_code stored),
                        pre-selected to the turn's existing intent_label if already set
        The row template should call back up with the turn id + chosen label_code on
        DropDown change (e.g. via `self.parent.raise_event('x-label-changed', ...)`
        or by giving the RepeatingPanel form a method the row calls directly).
  - Button              name: done_button         text: "Done annotating"  role: "btn-uga"

Suggested instructions text:
  "Below is every turn from your dialogues. For each one, pick the label that best matches
   what the speaker was doing in that turn — not what they said word-for-word, but their
   intent. If a turn feels like it could fit two labels, pick the one that feels closest;
   there's often no single perfect answer, and that's fine."
"""
from ._anvil_designer import AnnotationFormTemplate
from anvil import *
import anvil.server


class AnnotationForm(AnnotationFormTemplate):
  def __init__(self, room_code, student_name, **properties):
    self.init_components(**properties)
    self.room_code = room_code
    self.student_name = student_name

    self.intent_options = anvil.server.call('get_intent_labels')
    self.turns = anvil.server.call('get_turns_for_annotation', room_code)
    self._paint_repeater()

  def _paint_repeater(self):
    # Each row item carries both the turn data and the dropdown options,
    # so the row template can render "{dialogue_number} · {speaker}: text"
    # and a DropDown of (label_name, label_code) pairs.
    for t in self.turns:
      t['dropdown_items'] = [(o['label_name'], o['label_code']) for o in self.intent_options]
    self.turns_repeater.items = self.turns
    self._update_progress()

  def _update_progress(self):
    labeled = sum(1 for t in self.turns if t.get('intent_label'))
    self.progress_label.text = "{} / {} turns labeled".format(labeled, len(self.turns))

  def row_label_changed(self, turn_id, new_label_code, **event_args):
    """Called by each row template's DropDown 'change' handler, e.g.:
             self.parent.raise_event('x-label-changed', turn_id=..., new_label_code=...)
           and this form listens for it:
             self.turns_repeater.set_event_handler('x-label-changed', self.row_label_changed)
        """
    anvil.server.call('save_annotation', turn_id, new_label_code, self.student_name)
    for t in self.turns:
      if t['id'] == turn_id:
        t['intent_label'] = new_label_code
    self._update_progress()

  def done_button_click(self, **event_args):
    Notification("Thanks! Your annotations are saved.").show()
    open_form('Home')
