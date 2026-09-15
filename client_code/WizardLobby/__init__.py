"""
FORM: WizardLobby
Opened with: open_form('WizardLobby', student_name=name)

COMPONENTS TO ADD:
  - Label            name: title_label       text: "You're running the counter today"
  - Label            name: instructions_label text: plain instructions (see below)
  - Label            name: code_label         text: ""   font_size: 32, bold, role: "machine-intent-badge"
  - Label            name: waiting_label      text: "Waiting for your customer to join..."
  - Label            name: catalogue_title    text: "Your catalogue (customers can't see this)"
  - RepeatingPanel    name: catalogue_repeater  item_template: a simple ColumnPanel row
        showing item_name, category, price, flavor_notes, and "Out of stock" badge if
        in_stock is False. (Bind these via the RepeatingPanel's item template form,
        e.g. a small "CatalogueItemTemplate" form with labels bound to
        self.item['item_name'] etc.)
  - Timer             name: poll_timer         interval: 2  (seconds)

Suggested instructions text:
  "Share this code with your partner out loud or in the class chat. Once they join, you'll
   have 10 minutes together to run through a few quick orders. You can see the full candy
   catalogue below — your customer can't, so they'll have to ask you what's available."
"""
from ._anvil_designer import WizardLobbyTemplate
from anvil import *
import anvil.server


class WizardLobby(WizardLobbyTemplate):
  def __init__(self, student_name, **properties):
    self.init_components(**properties)
    self.student_name = student_name
    self.room_code = anvil.server.call('create_room', student_name)
    self.code_label.text = self.room_code
    self.catalogue_repeater.items = anvil.server.call('get_catalogue')
    self.poll_timer.interval = 2

  def poll_timer_tick(self, **event_args):
    status = anvil.server.call('get_room_status', self.room_code)
    if status['status'] == 'active':
      self.poll_timer.interval = 0  # stop polling
      open_form(
        'ChatSession',
        room_code=self.room_code,
        role='wizard',
        student_name=self.student_name,
      )
