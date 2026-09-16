"""
FORM: ChatBubbleTemplate — item template for a RepeatingPanel
One chat turn (speaker, message_text). Pure Data Bindings, no Python logic
needed.
"""
from ._anvil_designer import ChatBubbleTemplateTemplate
from anvil import *


class ChatBubbleTemplate(ChatBubbleTemplateTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
