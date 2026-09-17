"""
FORM: AnnotationForm — code-behind
Pair with AnnotationForm.html. Touches: progress_label, turns_repeater,
done_button.
Opened with: open_form('AnnotationForm', room_code=code, student_name=name)
"""
from ._anvil_designer import AnnotationFormTemplate
from anvil import *
import anvil.server
import anvil.js


class AnnotationForm(AnnotationFormTemplate):
  def __init__(self, room_code, student_name, **properties):
    self.init_components(**properties)
    self.progress_label.bold = False
    progress_node = anvil.js.get_dom_node(self.progress_label)
    progress_node.setAttribute("role", "status")
    progress_node.setAttribute("aria-live", "polite")
    progress_node.setAttribute("aria-atomic", "true")
    self.room_code = room_code
    self.student_name = student_name

    label_options = anvil.server.call('get_intent_labels')
    dropdown_items = [('Choose an intent...', None)] + [(o['label_name'], o['label_code']) for o in label_options]

    self.turns = anvil.server.call('get_turns_for_annotation', room_code)
    for t in self.turns:
      t['label_options'] = dropdown_items
      t['annotator_name'] = self.student_name

    self.turns_repeater.set_event_handler('x-annotated', self.row_annotated)
    self.turns_repeater.items = self.turns
    self._update_progress()

  def _update_progress(self):
    labeled = sum(1 for t in self.turns if t.get('intent_label'))
    self.progress_label.text = "Annotation progress: {} / {} turns labeled".format(labeled, len(self.turns))

  def row_annotated(self, **event_args):
    self._update_progress()

  @handle("done_button", "click")
  def done_button_click(self, **event_args):
    Notification("Thanks! Your annotations are saved.").show()
    open_form('Home')
