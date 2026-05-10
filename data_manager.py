import json
import os
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(__file__), "travel_data.json")

DEFAULT_DATA = {
    "trip_name": "我的日本旅遊",
    "total_budget_twd": 50000,
    "exchange_rates": {
        "JPY": 0.215,   # 1 JPY = 0.215 TWD
        "USD": 32.0,    # 1 USD = 32 TWD
        "EUR": 35.0,    # 1 EUR = 35 TWD
        "KRW": 0.024,  # 1 KRW = 0.024 TWD
    },
    "itinerary": [],
    "expenses": []
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_itinerary_item(date, time_str, location, activity, notes=""):
    data = load_data()
    item = {
        "id": datetime.now().isoformat(),
        "date": date,
        "time": time_str,
        "location": location,
        "activity": activity,
        "notes": notes
    }
    data["itinerary"].append(item)
    save_data(data)

def delete_itinerary_item(item_id):
    data = load_data()
    data["itinerary"] = [i for i in data["itinerary"] if i["id"] != item_id]
    save_data(data)

def add_expense(date, category, description, amount, currency):
    data = load_data()
    rate = data["exchange_rates"].get(currency, 1.0)
    amount_twd = round(amount * rate, 1) if currency != "TWD" else amount
    expense = {
        "id": datetime.now().isoformat(),
        "date": date,
        "category": category,
        "description": description,
        "amount_original": amount,
        "currency": currency,
        "amount_twd": amount_twd
    }
    data["expenses"].append(expense)
    save_data(data)

def delete_expense(expense_id):
    data = load_data()
    data["expenses"] = [e for e in data["expenses"] if e["id"] != expense_id]
    save_data(data)

def update_expense(expense_id, new_date, new_category, new_description, new_amount, new_currency):
    data = load_data()
    rate = data["exchange_rates"].get(new_currency, 1.0)
    amount_twd = round(new_amount * rate, 1) if new_currency != "TWD" else new_amount
    for e in data["expenses"]:
        if e["id"] == expense_id:
            e["date"] = new_date
            e["category"] = new_category
            e["description"] = new_description
            e["amount_original"] = new_amount
            e["currency"] = new_currency
            e["amount_twd"] = amount_twd
            break
    save_data(data)


def get_total_spent_twd(data):
    return sum(e["amount_twd"] for e in data["expenses"])

def get_expenses_by_category(data):
    categories = {}
    for e in data["expenses"]:
        cat = e["category"]
        categories[cat] = categories.get(cat, 0) + e["amount_twd"]
    return categories

def get_expenses_by_date(data):
    by_date = {}
    for e in data["expenses"]:
        d = e["date"]
        by_date[d] = by_date.get(d, 0) + e["amount_twd"]
    return dict(sorted(by_date.items()))
