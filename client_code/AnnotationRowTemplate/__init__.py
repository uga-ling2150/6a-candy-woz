"""
FORM: AnnotationRowTemplate — item template for a RepeatingPanel
One turn to label. self.item carries: id, dialogue_number, turn_index,
speaker, message_text, intent_label, annotator_name, label_options
(the last two are attached by AnnotationForm before setting .items).
Touches: intent_dropdown.
"""
from ._anvil_designer import AnnotationRowTemplateTemplate
from anvil import *
import anvil.server
import anvil.js


class AnnotationRowTemplate(AnnotationRowTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    node = anvil.js.get_dom_node(self.intent_dropdown)
    if node.tagName.lower() != "select":
      node = node.querySelector("select")
    node.setAttribute("aria-label", "Intent for dialogue {}, turn {} ({}): {}".format(self.item.get("dialogue_number", ""), self.item.get("turn_index", ""), self.item.get("speaker", ""), self.item.get("message_text", "")))

  @handle("intent_dropdown", "change")
  def intent_dropdown_change(self, **event_args):
    anvil.server.call(
      'save_annotation',
      self.item['id'],
      self.item['intent_label'],
      self.item['annotator_name'],
    )
    self.parent.raise_event('x-annotated')
