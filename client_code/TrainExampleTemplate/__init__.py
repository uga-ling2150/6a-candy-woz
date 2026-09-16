"""
FORM: TrainExampleTemplate — item template for a RepeatingPanel
One labeled training turn (speaker, text, label). Pure Data Bindings, no
Python logic needed.
"""
from ._anvil_designer import TrainExampleTemplateTemplate
from anvil import *


class TrainExampleTemplate(TrainExampleTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
