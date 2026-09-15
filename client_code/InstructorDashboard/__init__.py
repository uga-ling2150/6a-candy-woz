"""
FORM: InstructorDashboard — code-behind
Pair with InstructorDashboard.html. Touches: train_button, status_label,
results_panel, accuracy_label, train_size_label, train_label_counts_repeater,
train_examples_repeater, test_results_repeater. The "How does this actually
work?" explainer is a plain HTML <details>/<summary> in InstructorDashboard.html,
so no toggle button or Python is needed for it.
"""
from ._anvil_designer import InstructorDashboardTemplate
from anvil import *
import anvil.server


class InstructorDashboard(InstructorDashboardTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.results_panel.visible = False

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