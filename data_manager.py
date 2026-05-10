import json
import os
import re
import uuid
import hashlib

# 檔案路徑設定
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")
TRIPS_META_FILE = os.path.join(os.path.dirname(__file__), "trips_metadata.json")

def get_file_path(user_key):
    """根據旅程代碼取得資料檔案路徑"""
    safe_key = re.sub(r'[^\w\u4e00-\u9fff]', '_', user_key)
    return os.path.join(os.path.dirname(__file__), f"travel_data_{safe_key}.json")

DEFAULT_DATA = {
    "trip_name": "我的新旅程",
    "total_budget_twd": 0,
    "exchange_rates": {
        "JPY": 0.215,
        "USD": 32.2,
        "EUR": 35.1,
        "KRW": 0.024
    },
    "itinerary": [],
    "expenses": [],
    "password": None
}

# ─── 使用者帳號管理 ───────────────────────────────────────────

def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    users = _load_json(USERS_FILE, {})
    if username in users:
        return False, "使用者名稱已存在"
    
    # 生成唯一序號 (簡單起見用目前使用者數+1000)
    user_id = f"#{len(users) + 1001}"
    users[username] = {
        "password": hash_password(password),
        "user_id": user_id,
        "my_trips": [],    # 我建立的
        "joined_trips": [] # 我加入的
    }
    _save_json(USERS_FILE, users)
    return True, user_id

def login_user(username, password):
    users = _load_json(USERS_FILE, {})
    if username not in users:
        return None, "找不到使用者"
    if users[username]["password"] != hash_password(password):
        return None, "密碼錯誤"
    return users[username], "登入成功"

def update_user_password(username, new_password):
    users = _load_json(USERS_FILE, {})
    if username in users:
        users[username]["password"] = hash_password(new_password)
        _save_json(USERS_FILE, users)
        return True, "密碼修改成功"
    return False, "使用者不存在"

# ─── 旅程管理 ─────────────────────────────────────────────────

def create_trip(owner_username, secret, trip_name, is_public=True, password=None):
    meta = _load_json(TRIPS_META_FILE, {})
    users = _load_json(USERS_FILE, {})
    
    if secret in meta:
        return False, "此旅程暗號已被使用，請換一個"
    
    owner_id = users[owner_username]["user_id"]
    
    # 建立中繼資料
    meta[secret] = {
        "owner_username": owner_username,
        "owner_id": owner_id,
        "trip_name": trip_name,
        "is_public": is_public,
        "password": password
    }
    _save_json(TRIPS_META_FILE, meta)
    
    # 更新使用者的旅程清單
    users[owner_username]["my_trips"].append(secret)
    _save_json(USERS_FILE, users)
    
    # 建立實際資料檔
    trip_data = DEFAULT_DATA.copy()
    trip_data["trip_name"] = trip_name
    trip_data["password"] = password
    save_data(trip_data, user_key=secret)
    
    return True, "旅程建立成功"

def join_trip(username, secret, password):
    meta = _load_json(TRIPS_META_FILE, {})
    users = _load_json(USERS_FILE, {})
    
    if secret not in meta:
        return False, "找不到此旅程暗號"
    
    trip_info = meta[secret]
    if not trip_info["is_public"]:
        return False, "此旅程為私人設定，無法加入"
    
    if trip_info["password"] and trip_info["password"] != password:
        return False, "密碼錯誤"
    
    # 更新使用者的加入清單
    if secret not in users[username]["joined_trips"] and secret not in users[username]["my_trips"]:
        users[username]["joined_trips"].append(secret)
        _save_json(USERS_FILE, users)
    
    return True, "成功加入旅程"

def get_trip_info(secret):
    meta = _load_json(TRIPS_META_FILE, {})
    return meta.get(secret)

# ─── 原有的資料存取功能 ───────────────────────────────────────

def load_data(user_key="default"):
    file_path = get_file_path(user_key)
    if not os.path.exists(file_path):
        return DEFAULT_DATA.copy()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_DATA.copy()

def save_data(data, user_key="default"):
    file_path = get_file_path(user_key)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_exists(user_key):
    return os.path.exists(get_file_path(user_key))

# ...其餘功能(itinerary, expenses)保持不變，直接從 app.py 呼叫即可...

def add_itinerary_item(date, time_str, location, activity, notes="", user_key="default"):
    data = load_data(user_key)
    item = {
        "id": str(uuid.uuid4()),
        "date": date,
        "time": time_str,
        "location": location,
        "activity": activity,
        "notes": notes
    }
    data["itinerary"].append(item)
    save_data(data, user_key)

def delete_itinerary_item(item_id, user_key="default"):
    data = load_data(user_key)
    data["itinerary"] = [item for item in data["itinerary"] if item["id"] != item_id]
    save_data(data, user_key)

def add_expense(date, category, description, amount_orig, currency, user_key="default"):
    data = load_data(user_key)
    rate = data["exchange_rates"].get(currency, 1.0)
    amount_twd = amount_orig * rate if currency != "TWD" else amount_orig
    
    item = {
        "id": str(uuid.uuid4()),
        "date": date,
        "category": category,
        "description": description,
        "amount_original": amount_orig,
        "currency": currency,
        "amount_twd": amount_twd
    }
    data["expenses"].append(item)
    save_data(data, user_key)

def delete_expense(expense_id, user_key="default"):
    data = load_data(user_key)
    data["expenses"] = [e for e in data["expenses"] if e["id"] != expense_id]
    save_data(data, user_key)

def update_expense(expense_id, date, category, description, amount_orig, currency, user_key="default"):
    data = load_data(user_key)
    rate = data["exchange_rates"].get(currency, 1.0)
    amount_twd = amount_orig * rate if currency != "TWD" else amount_orig
    
    for e in data["expenses"]:
        if e["id"] == expense_id:
            e.update({
                "date": date,
                "category": category,
                "description": description,
                "amount_original": amount_orig,
                "currency": currency,
                "amount_twd": amount_twd
            })
            break
    save_data(data, user_key)

def update_settings(new_name, new_budget, new_rates, user_key="default"):
    data = load_data(user_key)
    data["trip_name"] = new_name
    data["total_budget_twd"] = new_budget
    data["exchange_rates"] = new_rates
    save_data(data, user_key)

def get_expenses_by_category(data):
    by_cat = {}
    for e in data["expenses"]:
        cat = e["category"]
        by_cat[cat] = by_cat.get(cat, 0) + e["amount_twd"]
    return by_cat

def get_expenses_by_date(data):
    by_date = {}
    for e in data["expenses"]:
        d = e["date"]
        by_date[d] = by_date.get(d, 0) + e["amount_twd"]
    # 排序日期
    return dict(sorted(by_date.items()))

def delete_user(username):
    """刪除使用者帳號"""
    db = _load_json(USERS_FILE, {})
    if username in db:
        del db[username]
        _save_json(USERS_FILE, db)
        return True, "帳號已成功刪除"
    return False, "找不到該使用者"
