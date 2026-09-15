"""
FORM: Home  (set as the app's startup form)

COMPONENTS TO ADD (drag from Toolbox onto a ColumnPanel with role "wrap"):
  - Label            name: title_label        text: "Georgia Candy — Wizard of Oz Lab"
  - Label            name: subtitle_label      text: short friendly intro (see below)
  - Label            name: name_label          text: "Your name"
  - TextBox          name: name_box            placeholder: "e.g. Sam"
  - Label            name: role_label          text: "I am the..."
  - RadioButton      name: role_wizard         text: "Wizard (candy store worker)"  group_name: "role"
  - RadioButton      name: role_human          text: "Human (customer)"             group_name: "role"
  - RadioButton      name: role_instructor     text: "Instructor"                   group_name: "role"
  - TextBox          name: instructor_code_box placeholder: "Instructor passcode"  visible: False
  - Label            name: error_label         text: ""   foreground: var(--uga-red)  visible: False
  - Button           name: continue_button     text: "Continue"  role: "btn-uga"

Suggested subtitle text (plain language, no jargon):
  "You'll be paired up to roleplay a conversation at a candy store. One of you runs the
   counter, one of you is the customer. It only takes a few minutes, and there's no wrong way
   to talk — just talk normally."
"""
from ._anvil_designer import HomeTemplate
from anvil import *
import anvil.server


class Home(HomeTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.role_instructor.set_event_handler('change', self.role_changed)
    self.role_wizard.set_event_handler('change', self.role_changed)
    self.role_human.set_event_handler('change', self.role_changed)

  def role_changed(self, **event_args):
    self.instructor_code_box.visible = self.role_instructor.selected

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
