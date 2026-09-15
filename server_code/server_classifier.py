"""
Server Module: server_classifier
A from-scratch bag-of-words multinomial Naive Bayes classifier (no external
ML libraries) so the whole training/prediction pipeline is visible and
explainable to students. Deliberately simplified: no stemming, no smoothing
tricks beyond basic Laplace add-1, no stopword removal — the point is to
make the mechanics legible, not to be production-grade NLP.
"""
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import math
import re
from collections import defaultdict, Counter


def _tokenize(text):
  return re.findall(r"[a-z']+", text.lower())


class SimpleNaiveBayes:
  """Multinomial Naive Bayes over bag-of-words counts, Laplace add-1 smoothing."""

  def __init__(self):
    self.classes = []
    self.class_doc_counts = Counter()
    self.class_word_counts = defaultdict(Counter)
    self.class_total_words = Counter()
    self.vocab = set()

  def fit(self, texts, labels):
    self.classes = sorted(set(labels))
    for text, label in zip(texts, labels):
      self.class_doc_counts[label] += 1
      for word in _tokenize(text):
        self.vocab.add(word)
        self.class_word_counts[label][word] += 1
        self.class_total_words[label] += 1

  def predict(self, text):
    """Returns (predicted_label, {label: probability, ...}) using log-space
        Naive Bayes, converted back to normalized probabilities at the end."""
    total_docs = sum(self.class_doc_counts.values())
    vocab_size = max(len(self.vocab), 1)
    words = _tokenize(text)

    log_scores = {}
    for c in self.classes:
      log_prior = math.log(self.class_doc_counts[c] / total_docs)
      log_likelihood = 0.0
      denom = self.class_total_words[c] + vocab_size  # Laplace smoothing
      for w in words:
        count = self.class_word_counts[c][w]
        log_likelihood += math.log((count + 1) / denom)
      log_scores[c] = log_prior + log_likelihood

      # Convert log scores to normalized probabilities (softmax-style, numerically stable)
    max_log = max(log_scores.values())
    exp_scores = {c: math.exp(s - max_log) for c, s in log_scores.items()}
    total = sum(exp_scores.values())
    probs = {c: exp_scores[c] / total for c in self.classes}

    predicted = max(probs, key=probs.get)
    return predicted, probs


@anvil.server.callable
def train_and_test_classifier():
  """
    Pulls every annotated student turn as training data, trains the classifier,
    then predicts every instructor-authored test_cases row. Returns everything
    the InstructorDashboard needs to render training data + test results
    side by side, plus overall accuracy.
    """
  # --- Training data: every turn a student has labeled ---
  labeled_rows = app_tables.turns.search(intent_label=q.not_(None))
  train_texts, train_labels, train_display = [], [], []
  for r in labeled_rows:
    if not r["intent_label"]:
      continue
    train_texts.append(r["message_text"])
    train_labels.append(r["intent_label"])
    train_display.append(
      {
        "text": r["message_text"],
        "speaker": r["speaker"],
        "label": r["intent_label"],
      }
    )

  if len(train_texts) < 5:
    return {
      "error": "Not enough annotated data yet — need at least a handful of "
      "labeled turns before training. Check that annotation is complete.",
    }

  model = SimpleNaiveBayes()
  model.fit(train_texts, train_labels)

  # --- Test data: instructor's preset sentences ---
  test_rows = app_tables.test_cases.search()
  test_results = []
  correct = 0
  total = 0
  for r in test_rows:
    predicted, probs = model.predict(r["text"])
    is_correct = predicted == r["true_label"]
    correct += int(is_correct)
    total += 1
    # Sort class probabilities for display, most likely first
    sorted_probs = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    test_results.append(
      {
        "text": r["text"],
        "true_label": r["true_label"],
        "predicted_label": predicted,
        "correct": is_correct,
        "confidence": sorted_probs[0][1],
        "top_scores": sorted_probs[:3],  # top 3 classes for a mini breakdown
      }
    )

  accuracy = (correct / total) if total else None

  # Class balance in the training set — useful context for the discussion
  label_counts = Counter(train_labels)

  return {
    "training_data": train_display,
    "training_label_counts": dict(label_counts),
    "training_size": len(train_texts),
    "test_results": test_results,
    "accuracy": accuracy,
  }