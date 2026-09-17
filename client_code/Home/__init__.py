"""
FORM: Home — code-behind
Pair with Home.html. Only the components named there (name_box, role_wizard,
role_human, role_instructor, instructor_code_box, error_label, continue_button)
are touched by Python — everything else in Home.html is static markup.
"""
from ._anvil_designer import HomeTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.js


class Home(HomeTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    document = anvil.js.window.document
    banner = document.querySelector("#anvil-header")
    if banner:
      banner.setAttribute("role", "banner")
    for selector in ["#anvil-header img", "#anvil-badge img"]:
      image = document.querySelector(selector)
      if image:
        image.setAttribute("alt", "Anvil")
    badge = document.querySelector("#anvil-badge")
    if badge:
      badge.setAttribute("aria-label", "Built with Anvil")
    for component, name in [(self.name_box, 'Your name'), (self.instructor_code_box, 'Instructor passcode')]:
      node = anvil.js.get_dom_node(component)
      if node.tagName.lower() != 'input':
        node = node.querySelector('input')
      node.setAttribute('aria-label', name)
    error_node = anvil.js.get_dom_node(self.error_label)
    error_node.setAttribute('role', 'alert')
    self.role_instructor.set_event_handler('change', self.role_changed)
    self.role_wizard.set_event_handler('change', self.role_changed)
    self.role_human.set_event_handler('change', self.role_changed)

  def role_changed(self, **event_args):
    self.instructor_code_box.visible = self.role_instructor.selected

  @handle("continue_button", "click")
  def continue_button_click(self, **event_args):
    self.error_label.visible = False
    name = self.name_box.text.strip() if self.name_box.text else ""
    if not name:
      self.error_label.text = "Please enter your name first."
      self.error_label.visible = True
      return

    if self.role_wizard.selected:
      open_form('WizardLobby', student_name=name)
    elif self.role_human.selected:
      open_form('HumanLobby', student_name=name)
    elif self.role_instructor.selected:
      code_ok = anvil.server.call('check_instructor_code', self.instructor_code_box.text)
      if not code_ok:
        self.error_label.text = "That instructor passcode isn't right."
        self.error_label.visible = True
        return
      open_form('InstructorDashboard')
    else:
      self.error_label.text = "Pick a role to continue."
      self.error_label.visible = True