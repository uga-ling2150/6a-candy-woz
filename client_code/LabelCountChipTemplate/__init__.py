"""
FORM: LabelCountChipTemplate — item template for a RepeatingPanel
One "label: count" chip in the training-data class-balance row. Pure Data
Binding, no Python logic needed.
"""
from ._anvil_designer import LabelCountChipTemplateTemplate
from anvil import *


class LabelCountChipTemplate(LabelCountChipTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
