"""
FORM: InstructorDashboard
Opened with: open_form('InstructorDashboard')

COMPONENTS TO ADD:
  - Label              name: title_label          text: "Instructor Dashboard"
  - Button              name: train_button          text: "Train & Test Classifier"
                         role: "btn-uga"
  - Label               name: status_label          text: ""  visible: False
  - Label               name: accuracy_label        text: ""  role: "status-success"
  - ColumnPanel         name: results_panel          visible: False
      -- Two side-by-side columns (use a LinearPanel/GridPanel with two ColumnPanels) --
      Left column ("Training Data"):
        - Label          name: train_title           text: "Training data (from your class)"
        - Label          name: train_size_label       text: ""
        - RepeatingPanel  name: train_label_counts_repeater
              item_template: chip showing label name + count, using .chip CSS class
        - RepeatingPanel  name: train_examples_repeater
              item_template: row showing speaker + text + assigned label
      Right column ("Test Results"):
        - Label          name: test_title            text: "Test sentences (instructor-authored)"
        - RepeatingPanel  name: test_results_repeater
              item_template: "TestResultRowTemplate" showing:
                - the test sentence
                - true label vs. predicted label
                - ✓ / ✗ character (not color alone) for correct/incorrect
                - a confidence bar using .confidence-bar-container /.confidence-fill,
                  PLUS a numeric percentage label next to it
                - top 3 class scores as a small breakdown (optional, for discussion)
  - Label               name: reflection_title      text: "Class discussion"
  - Label               name: reflection_prompts     text: (see below, multi-line)
  - ColumnPanel         name: technical_details_panel  visible: False  (collapsible)
      - Button           name: toggle_technical_button  text: "How does this actually work?"
      - Label            name: technical_explainer_label text: (see below)

Suggested reflection prompts (static text, discussed live in class, not saved anywhere):
  "Look at the test sentences the model got wrong. What do they have in common? Notice
   whether short sentences with few 'candy words' (like confirmations or corrections) are
   harder to classify than ones that mention specific items. This model only looks at which
   words appear, not their order or context — what does that suggest about its limits, and
   what would you need to give it to fix those specific mistakes?"

Suggested technical_explainer_label text (kept collapsed by default):
  "This uses a simplified 'bag-of-words' Naive Bayes classifier: it counts how often each
   word appears with each intent label in the training data, then for a new sentence,
   multiplies together how likely each of its words is under each label (with a small
   correction called Laplace smoothing so unseen words don't break the math), and picks the
   label with the highest resulting probability. It has no idea about word order, grammar,
   or meaning beyond word counts — which is exactly why certain sentences trip it up."
"""
from ._anvil_designer import InstructorDashboardTemplate
from anvil import *
import anvil.server


class InstructorDashboard(InstructorDashboardTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.results_panel.visible = False
    self.technical_details_panel.visible = False

  def train_button_click(self, **event_args):
    self.status_label.text = "Training..."
    self.status_label.visible = True
    self.results_panel.visible = False

    result = anvil.server.call('train_and_test_classifier')

    if 'error' in result:
      self.status_label.text = result['error']
      return

    self.status_label.visible = False
    self.results_panel.visible = True

    self.train_size_label.text = "{} labeled turns used for training".format(
      result['training_size']
    )
    self.train_label_counts_repeater.items = [
      {"label": k, "count": v} for k, v in result['training_label_counts'].items()
    ]
    self.train_examples_repeater.items = result['training_data']

    self.test_results_repeater.items = result['test_results']

    if result['accuracy'] is not None:
      self.accuracy_label.text = "Accuracy on test sentences: {:.0%}".format(
        result['accuracy']
      )
      self.accuracy_label.visible = True

  def toggle_technical_button_click(self, **event_args):
    self.technical_details_panel.visible = not self.technical_details_panel.visible
