"""
Server Module: server_seed
One-time bootstrap for the fixed intent taxonomy, candy catalogue, and
instructor test sentences. Call seed_reference_data() once (e.g. from the
IDE's server console) before class. Safe to call again later — each table
is keyed off a natural column, so re-running only fills in rows that are
still missing instead of duplicating them.
"""
import anvil.server
from anvil.tables import app_tables

INTENT_LABELS = [
  {
    "label_code": "greeting",
    "label_name": "Greeting",
    "description": "Opening a conversation, no request yet",
    "example_phrase": "Hi, how's it going?",
  },
  {
    "label_code": "order_item",
    "label_name": "Order an Item",
    "description": "Asking to buy or get something specific",
    "example_phrase": "Can I get a bag of the sour gummies?",
  },
  {
    "label_code": "ask_price",
    "label_name": "Ask About Price",
    "description": "Asking how much something costs",
    "example_phrase": "How much is the chocolate bark?",
  },
  {
    "label_code": "ask_availability",
    "label_name": "Ask If Something's In Stock",
    "description": "Asking whether an item exists / is available",
    "example_phrase": "Do you have any peach gummies left?",
  },
  {
    "label_code": "ask_recommendation",
    "label_name": "Ask For a Recommendation",
    "description": "Asking what's good, popular, or worth trying",
    "example_phrase": "What's your best seller?",
  },
  {
    "label_code": "modify_order",
    "label_name": "Change an Order",
    "description": "Adjusting a request already made",
    "example_phrase": "Actually, make that two bags instead",
  },
  {
    "label_code": "confirm",
    "label_name": "Confirm / Agree",
    "description": "Agreeing to something or confirming a detail",
    "example_phrase": "Yes, that's right",
  },
  {
    "label_code": "thanks_closing",
    "label_name": "Thanks / Closing",
    "description": "Wrapping up the interaction",
    "example_phrase": "Thanks, that's everything!",
  },
  {
    "label_code": "small_talk",
    "label_name": "Small Talk",
    "description": "Friendly chat unrelated to ordering",
    "example_phrase": "Go Dawgs, by the way",
  },
]

CATALOGUE_ITEMS = [
  {
    "item_name": "UGA Gumdrops",
    "category": "Gummy & Chewy",
    "price": "$1.50",
    "flavor_notes": "Classic red-and-black gumdrops, sugar-dusted",
    "in_stock": True,
  },
  {
    "item_name": "Bulldog Bites",
    "category": "Chocolate",
    "price": "$3.00",
    "flavor_notes": "Milk chocolate malt balls",
    "in_stock": True,
  },
  {
    "item_name": "Sic 'Em Sours",
    "category": "Sour",
    "price": "$2.25",
    "flavor_notes": "Extra-sour rainbow belts",
    "in_stock": True,
  },
  {
    "item_name": "Hedges Honeycomb",
    "category": "Chocolate",
    "price": "$3.50",
    "flavor_notes": "Dark chocolate-covered honeycomb toffee",
    "in_stock": True,
  },
  {
    "item_name": "Between the Hedges Taffy",
    "category": "Gummy & Chewy",
    "price": "$1.75",
    "flavor_notes": "Assorted fruit taffy",
    "in_stock": True,
  },
  {
    "item_name": "Georgia Peach Gummies",
    "category": "Gummy & Chewy",
    "price": "$2.00",
    "flavor_notes": "Peach-flavored gummy rings",
    "in_stock": True,
  },
  {
    "item_name": "Chapel Bell Bark",
    "category": "Chocolate",
    "price": "$4.00",
    "flavor_notes": "White and dark chocolate swirl bark with almonds",
    "in_stock": True,
  },
  {
    "item_name": "Sanford Stadium Mix",
    "category": "Popcorn & Mix",
    "price": "$3.25",
    "flavor_notes": "Candy-coated popcorn and pretzel mix",
    "in_stock": True,
  },
  {
    "item_name": "Athens Orange Slices",
    "category": "Sour",
    "price": "$1.50",
    "flavor_notes": "Classic sugared orange candy slices",
    "in_stock": True,
  },
  {
    "item_name": "Damn Good Dawg Chews",
    "category": "Gummy & Chewy",
    "price": "$2.50",
    "flavor_notes": "Caramel chews, seasonal — check stock",
    "in_stock": False,
  },
]

TEST_CASES = [
  {
    "text": "Hi! Can I get some sour gummies?",
    "true_label": "order_item",
    "difficulty_note": "Easy — close to a typical training phrase",
  },
  {
    "text": "How much for the chocolate bark?",
    "true_label": "ask_price",
    "difficulty_note": "Easy — clear price question",
  },
  {
    "text": "Do y'all still have the orange slices?",
    "true_label": "ask_availability",
    "difficulty_note": "Medium — regional phrasing (\"y'all\"), no exact \"do you have\"",
  },
  {
    "text": "What would you recommend for someone who loves sour candy?",
    "true_label": "ask_recommendation",
    "difficulty_note": "Hard — long, embeds \"sour candy\" which BoW may associate with order_item",
  },
  {
    "text": "Oh actually, scratch that, just one bag",
    "true_label": "modify_order",
    "difficulty_note": "Hard — no candy words at all, relies on function words",
  },
  {
    "text": "That works, thanks so much!",
    "true_label": "confirm",
    "difficulty_note": "Hard — overlaps with thanks_closing",
  },
  {
    "text": "Go Dawgs! Beautiful day out here",
    "true_label": "small_talk",
    "difficulty_note": "Medium — clearly off-topic but shares vocabulary with greeting",
  },
  {
    "text": "Alright, I think that's everything I need",
    "true_label": "thanks_closing",
    "difficulty_note": "Hard — no explicit \"thanks\", relies on phrasing pattern",
  },
  {
    "text": "Hey there, how's your day going?",
    "true_label": "greeting",
    "difficulty_note": "Easy — classic opener",
  },
  {
    "text": "I'll take two of the honeycomb ones please",
    "true_label": "order_item",
    "difficulty_note": "Medium — refers to item by partial/descriptive name, not full catalogue name",
  },
]


@anvil.server.callable
def seed_reference_data():
  """Populate intent_labels, catalogue_items, and test_cases if missing.
  Returns a dict of how many rows were added to each table."""
  added = {"intent_labels": 0, "catalogue_items": 0, "test_cases": 0}

  for row in INTENT_LABELS:
    if not app_tables.intent_labels.get(label_code=row["label_code"]):
      app_tables.intent_labels.add_row(**row)
      added["intent_labels"] += 1

  for row in CATALOGUE_ITEMS:
    if not app_tables.catalogue_items.get(item_name=row["item_name"]):
      app_tables.catalogue_items.add_row(**row)
      added["catalogue_items"] += 1

  for row in TEST_CASES:
    if not app_tables.test_cases.get(text=row["text"]):
      app_tables.test_cases.add_row(**row)
      added["test_cases"] += 1

  return added
