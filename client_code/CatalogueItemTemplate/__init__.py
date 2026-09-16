"""
FORM: CatalogueItemTemplate — item template for a RepeatingPanel
One row of the candy catalogue (item_name, category, price, flavor_notes,
in_stock). Pure Data Bindings, no Python logic needed.
"""
from ._anvil_designer import CatalogueItemTemplateTemplate
from anvil import *


class CatalogueItemTemplate(CatalogueItemTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
