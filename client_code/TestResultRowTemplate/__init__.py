"""
FORM: TestResultRowTemplate — item template for a RepeatingPanel
One instructor test sentence result (text, true_label, predicted_label,
correct, confidence, top_scores). Pure Data Bindings, no Python logic
needed.
"""
from ._anvil_designer import TestResultRowTemplateTemplate
from anvil import *


class TestResultRowTemplate(TestResultRowTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
