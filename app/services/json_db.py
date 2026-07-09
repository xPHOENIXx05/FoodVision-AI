import json
import os


def load_json_db(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except:
            return []


def save_json_db(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def init_db(db_users_path, db_foods_path, db_logs_path, db_audit_path):
    if not os.path.exists(db_users_path):
        save_json_db(db_users_path, [])
    if not os.path.exists(db_foods_path):
        save_json_db(db_foods_path, [])
    if not os.path.exists(db_logs_path):
        save_json_db(db_logs_path, [])
    if not os.path.exists(db_audit_path):
        save_json_db(db_audit_path, [])
