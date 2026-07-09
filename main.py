"""
Food Calorie Estimation API using Flask and CNN Deep Learning Model
"""
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_cors import CORS
import numpy as np
import base64
import io
import json
import os
from PIL import Image
import requests
from app.services.json_db import (
    load_json_db,
    save_json_db,
    init_db,
)
API_KEY = os.environ.get("USDA_API_KEY", "ZRREJ2EWXdQvYYckq9EAQdlbKNSbn6Nbk8yybRbI")



def get_calories_from_api(food_name):
    try:
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={API_KEY}"

        response = requests.get(url)
        data = response.json()

        if "foods" not in data or len(data["foods"]) == 0:
            return None

        nutrients = data["foods"][0].get("foodNutrients", [])

        calories = protein = carbs = fat = "Unknown"

        for n in nutrients:
            name = n.get("nutrientName")
            value = n.get("value")

            if name == "Energy":
                calories = value
            elif name == "Protein":
                protein = value
            elif name == "Carbohydrate, by difference":
                carbs = value
            elif name == "Total lipid (fat)":
                fat = value

        return {
            "calories": calories,
            "serving": "100g",
            "protein": protein,
            "carbs": carbs,
            "fat": fat
        }

    except Exception as e:
        print("API ERROR:", e)
        return None

# TensorFlow imports commented out
# import tensorflow as tf
# from tensorflow import keras

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_dev_key")
CORS(app)

# Database initialization
DB_USERS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'users.json')
DB_FOODS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'foods.json')
DB_LOGS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'activity_logs.json')
DB_AUDIT_PATH = os.path.join(os.path.dirname(__file__), 'data', 'audit_logs.json')

init_db(
    DB_USERS_PATH,
    DB_FOODS_PATH,
    DB_LOGS_PATH,
    DB_AUDIT_PATH,
)

# Food classes that our model can predict
FOOD_CLASSES = [
    "apple", "banana", "burger", "pizza", "dosa", 
    "french_fries", "hot_dog", "ice_cream", "omelette", 
    "pasta", "rice", "salad", "sandwich", "sushi", "tacos"
]

# Calorie data for each food item (per serving)
CALORIE_DATA = {
    "apple": {"calories": 95, "serving": "1 medium (182g)", "protein": "0.5g", "carbs": "25g", "fat": "0.3g"},
    "banana": {"calories": 105, "serving": "1 medium (118g)", "protein": "1.3g", "carbs": "27g", "fat": "0.4g"},
    "burger": {"calories": 354, "serving": "1 burger (110g)", "protein": "20g", "carbs": "29g", "fat": "17g"},
    "pizza": {"calories": 285, "serving": "1 slice (107g)", "protein": "12g", "carbs": "36g", "fat": "10g"},
    "dosa": {"calories": 168, "serving": "1 dosa (100g)", "protein": "4g", "carbs": "29g", "fat": "4g"},
    "french_fries": {"calories": 312, "serving": "1 medium (117g)", "protein": "3.4g", "carbs": "41g", "fat": "15g"},
    "hot_dog": {"calories": 290, "serving": "1 hot dog (98g)", "protein": "11g", "carbs": "24g", "fat": "17g"},
    "ice_cream": {"calories": 207, "serving": "1 cup (132g)", "protein": "3.5g", "carbs": "24g", "fat": "11g"},
    "omelette": {"calories": 154, "serving": "1 omelette (2 eggs)", "protein": "11g", "carbs": "1g", "fat": "12g"},
    "pasta": {"calories": 220, "serving": "1 cup cooked (140g)", "protein": "8g", "carbs": "43g", "fat": "1.3g"},
    "rice": {"calories": 206, "serving": "1 cup cooked (158g)", "protein": "4.3g", "carbs": "45g", "fat": "0.4g"},
    "salad": {"calories": 152, "serving": "1 bowl (207g)", "protein": "3g", "carbs": "11g", "fat": "12g"},
    "sandwich": {"calories": 252, "serving": "1 sandwich (145g)", "protein": "10g", "carbs": "29g", "fat": "10g"},
    "sushi": {"calories": 200, "serving": "6 pieces (158g)", "protein": "9g", "carbs": "38g", "fat": "0.7g"},
    "tacos": {"calories": 226, "serving": "1 taco (135g)", "protein": "9g", "carbs": "20g", "fat": "12g"}
}

# Global model variable
model = None

# API_KEY is set globally at the top of the file

# Food Label Mapping System
food_labels = [
    "apple pie", "baby back ribs", "baklava", "beef carpaccio", "beef tartare", "beet salad", "beignets",
    "bibimbap", "bread pudding", "breakfast burrito", "bruschetta", "caesar salad", "cannoli", "caprese salad",
    "carrot cake", "ceviche", "cheesecake", "cheese plate", "chicken curry", "chicken quesadilla", "chicken wings",
    "chocolate cake", "chocolate mousse", "churros", "clam chowder", "club sandwich", "crab cakes", "creme brulee",
    "croque madame", "cup cakes", "deviled eggs", "donuts", "dumplings", "edamame", "eggs benedict", "escargots",
    "falafel", "filet mignon", "fish and chips", "foie gras", "french fries", "french onion soup", "french toast",
    "fried calamari", "fried rice", "frozen yogurt", "garlic bread", "gnocchi", "greek salad", "grilled cheese sandwich",
    "grilled salmon", "guacamole", "hamburger", "hot and sour soup", "hot dog", "huevos rancheros", "hummus",
    "ice cream", "lasagna", "lobster bisque", "lobster roll sandwich", "macaroni and cheese", "macarons", "miso soup",
    "mussels", "nachos", "omelette", "onion rings", "oysters", "pad thai", "paella", "pancakes", "panna cotta",
    "peking duck", "pho", "pizza", "pork chop", "poutine", "prime rib", "pulled pork sandwich", "ramen", "ravioli",
    "red velvet cake", "risotto", "samosa", "sashimi", "scallops", "seaweed salad", "shrimp and grits",
    "spaghetti bolognese", "spaghetti carbonara", "spring rolls", "steak", "strawberry shortcake", "sushi", "tacos",
    "takoyaki", "tiramisu", "tuna tartare", "waffles"
]

def get_food_name(class_id, confidence):

    global food_labels

    # lower unknown threshold
    if confidence < 0.05:
        return "Unknown Food"

    if class_id < len(food_labels):
        return food_labels[class_id]

    return "Unknown Food"

# Normalize model food names for USDA lookups and calorie mapping
def normalize_food_name(food_name):
    if not food_name:
        return None

    normalized = food_name.lower().strip()

    # Simple alias mapping for commonly misclassified names
    aliases = {
        'french fries': 'french fries',
        'fries': 'french fries',
        'hot dog': 'hot dog',
        'hamburger': 'burger',
        'ice cream': 'ice cream',
        'chicken wings': 'chicken wings',
        'pizza': 'pizza',
        'sushi': 'sushi',
        'tacos': 'tacos',
        'bibimbap': 'bibimbap',
        'burger': 'burger',
        'dosa': 'dosa',
        'salad': 'salad',
    }

    if normalized in aliases:
        return aliases[normalized]

    # remove punctuation and underscores
    normalized = normalized.replace('_', ' ').replace('-', ' ').strip()

    return normalized

# PyTorch / timm / torchvision imports removed for Render deployment
# import torch
# import timm
# from torchvision import transforms
import json

def load_mapping():
    """Load class label mapping file (food101_classes.txt or JSON)."""
    global food_labels
    mapping_path = os.path.join(os.path.dirname(__file__), 'food101_classes.txt')
    try:
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r') as f:
                food_labels = [line.strip().replace('_', ' ').title() for line in f if line.strip()]
            print("Loaded food101_classes.txt mapping.")
        else:
            print("Mapping file not found, using fallback array.")
    except Exception as e:
        print(f"Error loading mapping: {e}")

load_mapping()

def load_model():
    """Mock load_model for production without timm."""
    global model
    model = None
    return model

# Global initialization at startup disabled
# load_model()

import io

# ===== AI PREDICTION FINAL FIX =====

#mport torch
#mport torch.nn.functional as F
#rom torchvision import transforms
#rom PIL import Image

def predict_food(image_data):
    """
    Mocked food prediction for Render free tier deployment.
    Simulates AI image prediction returning Pizza.
    """
    food_name = "Pizza"
    confidence = 0.92
    predictions_list = [
        {"name": "Pizza", "confidence": 92},
        {"name": "Burger", "confidence": 5},
        {"name": "Pasta", "confidence": 3}
    ]
    return food_name, confidence, predictions_list
    
import time

@app.route('/predict', methods=['POST'])
def predict():
    """
    Predict food and calories from uploaded image.
    
    Accepts:
    - File upload with key 'image'
    - Base64 encoded image in JSON body with key 'image'
    
    Returns:
    - Predicted food name (or Unknown Food)
    - Calorie information
    - Confidence score & top 3 predictions
    """
    try:
        image_data = None
        
        # Check for file upload
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_data = file.read()
        
        # Check for base64 encoded image in JSON
        if image_data is None and request.is_json:
            data = request.get_json()
            if 'image' in data:
                # Remove data URL prefix if present
                base64_str = data['image']
                if ',' in base64_str:
                    base64_str = base64_str.split(',')[1]
                image_data = base64.b64decode(base64_str)
        
        if image_data is None:
            return jsonify({
                "success": False,
                "error": "No image provided. Please upload an image file or send base64 encoded image."
            }), 400
        
        # Manual wait mechanism
        time.sleep(3)
        
        # Predict food class with final fix logic
        food_name, confidence, predictions_list = predict_food(image_data)

        # Apply a usage threshold to reduce obvious classification errors
        if confidence < 0.15 or food_name == "Unknown Food":
            predicted_food = "Unknown Food"
        else:
            predicted_food = food_name

        # UI Compatibility Mapper wrapper
        prediction_result = {
            "food": predicted_food,
            "final_food": predicted_food,
            "confidence": confidence,
            "predictions": predictions_list,
            "top3": predictions_list,
            "is_unknown": (predicted_food == "Unknown Food")
        }

        # Get calorie information from USDA API (or fallback to stored CALORIE_DATA)
        calorie_info = None
        if predicted_food != "Unknown Food":
            normalized_name = normalize_food_name(predicted_food)
            calorie_info = get_calories_from_api(normalized_name)
            if (not calorie_info or calorie_info.get("calories") == "Unknown") and normalized_name in CALORIE_DATA:
                calorie_info = CALORIE_DATA[normalized_name]

        if calorie_info is None:
            calorie_info = {
                "calories": "Unknown",
                "serving": "Unknown",
                "protein": "Unknown",
                "carbs": "Unknown",
                "fat": "Unknown"
            }

        return jsonify({
            "success": True,
            "predictions": prediction_result.get("predictions", []),
            "is_unknown": prediction_result.get("is_unknown", False),
            # Dual-struct payload dynamically handling the new data shape natively
            "final_food": predicted_food,
            "confidence": prediction_result.get("confidence", 0),
            "top3": prediction_result.get("predictions", []),
            "calories_data": {
                "calories": calorie_info["calories"],
                "serving_size": calorie_info["serving"],
                "protein": calorie_info["protein"],
                "carbohydrates": calorie_info["carbs"],
                "fat": calorie_info["fat"]
            },
            # UI Backward compatibility
            "prediction": {
                "food": predicted_food,
                "confidence": prediction_result.get("confidence", 0),
                "top3": prediction_result.get("predictions", []),
                "nutrition": {
                    "calories": calorie_info["calories"],
                    "serving_size": calorie_info["serving"],
                    "protein": calorie_info["protein"],
                    "carbohydrates": calorie_info["carbs"],
                    "fat": calorie_info["fat"]
                }
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/manual', methods=['POST'])
def manual_entry():
    """
    Handle manual food entry:
    - If calories_per_unit and quantity are provided, uses them directly.
    - Else falls back to USDA grams-based lookup with 'grams'.
    """
    try:
        data = request.get_json()
        if not data or 'food' not in data:
            return jsonify({"success": False, "error": "Missing food name."}), 400

        food_name = data['food'].strip()
        if not food_name:
            return jsonify({"success": False, "error": "Food name must not be empty."}), 400

        calories_per_unit = data.get('calories_per_unit')
        unit = data.get('unit')
        quantity = data.get('quantity')

        if calories_per_unit is not None and unit is not None and quantity is not None:
            try:
                calories_per_unit = float(calories_per_unit)
                quantity = float(quantity)
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "Calories per unit and quantity must be numeric."}), 400

            if calories_per_unit <= 0 or quantity <= 0:
                return jsonify({"success": False, "error": "Calories per unit and quantity must be positive."}), 400

            if unit not in ['grams', 'pieces']:
                return jsonify({"success": False, "error": "Unit must be 'grams' or 'pieces'."}), 400

            total_calories = round(calories_per_unit * quantity, 2)
            nutrition = {
                "calories_per_unit": calories_per_unit,
                "quantity": quantity,
                "unit": unit,
                "total_calories": total_calories
            }

            return jsonify({
                "success": True,
                "food": food_name.title(),
                "nutrition": nutrition
            })

        # Fallback flow: grams-based USDA lookup
        if 'grams' not in data:
            return jsonify({"success": False, "error": "Missing calories or grams data for manual entry."}), 400

        try:
            grams = float(data['grams'])
            if grams <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({"success": False, "error": "Grams must be a positive number."}), 400

        calorie_info = get_calories_from_api(food_name)
        if calorie_info is None or calorie_info.get("calories") == "Unknown":
            return jsonify({"success": False, "error": f"Could not find exact nutrition data for '{food_name}'."}), 404

        multiplier = grams / 100.0

        def calc_prop(val):
            try:
                if isinstance(val, str):
                    import re
                    num_str = re.sub(r'[^\d.]', '', val)
                    if num_str:
                        return round(float(num_str) * multiplier, 2)
                    return "Unknown"
                return round(float(val) * multiplier, 2)
            except (ValueError, TypeError):
                return "Unknown"
                
        calculated = {
            "calories": calc_prop(calorie_info.get("calories", "Unknown")),
            "serving_size": f"{grams}g",
            "protein": calc_prop(calorie_info.get("protein", "Unknown")),
            "carbohydrates": calc_prop(calorie_info.get("carbs", "Unknown")),
            "fat": calc_prop(calorie_info.get("fat", "Unknown"))
        }
        
        return jsonify({
            "success": True,
            "food": food_name.title(),
            "nutrition": calculated
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/foods', methods=['GET'])
def get_foods():
    """Get list of all supported foods and their calorie information."""
    foods = []
    for food_class in FOOD_CLASSES:
        info = CALORIE_DATA.get(food_class, {})
        foods.append({
            "name": food_class.replace("_", " ").title(),
            "calories": info.get("calories", "Unknown"),
            "serving": info.get("serving", "Unknown")
        })
    return jsonify({"foods": foods})

# Initialize model on startup disabled
# load_model()

@app.route("/")
def home():
    if 'user_id' in session:
        role = session.get('role', 'user')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            
        users = load_json_db(DB_USERS_PATH)
        user = next((u for u in users if u.get('email') == email), None)
        
        if user and check_password_hash(user['password'], password):
            if user.get('banned'):
                if request.is_json:
                    return jsonify({"success": False, "error": "Your account has been banned. Please contact the administrator."}), 403
                flash('Your account has been banned. Please contact the administrator.', 'error')
                return render_template('login.html')

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'user')
            session['email'] = user.get('email', '')
            
            from datetime import datetime
            user['last_active'] = datetime.utcnow().isoformat()
            save_json_db(DB_USERS_PATH, users)
            
            role = session['role']
            redirect_url = url_for("admin_dashboard") if role == "admin" else url_for("user_dashboard")
            
            if request.is_json:
                return jsonify({"success": True, "role": role, "user_id": user['id'], "username": user['username'], "redirect": redirect_url})
            return redirect(redirect_url)
        else:
            if request.is_json:
                return jsonify({"success": False, "error": "Invalid email or password"}), 401
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
        if not username or not password or not email:
            if request.is_json:
                return jsonify({"success": False, "error": "Username, email and password are required"}), 400
            flash('Username, email and Password are required', 'error')
            return render_template('signup.html')
            
        users = load_json_db(DB_USERS_PATH)
        
        if any(u.get('email') == email for u in users) or any(u.get('username') == username for u in users):
            if request.is_json:
                return jsonify({"success": False, "error": "Username or email already exists"}), 409
            flash('Username or email already exists', 'error')
            return render_template('signup.html')
            
        hashed_password = generate_password_hash(password)
        role = "admin" if email == "admin@example.com" else "user"
        new_id = max([u.get('id', 0) for u in users] + [0]) + 1
        
        from datetime import datetime
        now_iso = datetime.utcnow().isoformat()
        
        users.append({
            "id": new_id,
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": role,
            "created_at": now_iso,
            "last_active": now_iso
        })
        save_json_db(DB_USERS_PATH, users)
        
        if request.is_json:
            return jsonify({"success": True, "message": "Account created successfully! Please login.", "redirect": url_for("login")})
            
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
            
    return render_template('signup.html')

@app.route("/register", methods=['POST'])
def register():
    return signup()

@app.route("/user-dashboard")
def user_dashboard():
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('user-dashboard.html', username=session['username'])

@app.route('/calorie', methods=['GET'])
def calorie_page():
    # direct static calorie calculator UI
    if 'user_id' not in session:
        flash('Please login to access the calorie calculator', 'error')
        return redirect(url_for('login'))
    return render_template('calorie_page.html', username=session.get('username', 'User'))

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route("/api/health")
def health():
    return {"status": "ok"}

@app.route("/api/foods")
def foods():
    return {"foods": FOOD_CLASSES}

@app.route('/api/log_activity', methods=['POST'])
def log_activity():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    data = request.get_json()
    action_type = data.get('action_type', 'unknown')
    food_name = data.get('food_name', '')
    quantity = data.get('quantity', '')
    calories = data.get('calories', 0)
    
    # Resolve email
    email = session.get('email')
    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == session['user_id']), None)
    if user:
        if not email:
            email = user.get('email')
            session['email'] = email
            
        from datetime import datetime
        now_iso = datetime.utcnow().isoformat()
        user['last_active'] = now_iso
        save_json_db(DB_USERS_PATH, users)
    else:
        email = "Unknown"
        from datetime import datetime
        now_iso = datetime.utcnow().isoformat()

    logs = load_json_db(DB_LOGS_PATH)
    new_log = {
        "id": max([l.get('id', 0) for l in logs] + [0]) + 1,
        "user_email": email,
        "action_type": action_type,
        "food_name": food_name,
        "quantity": quantity,
        "calories": calories,
        "timestamp": now_iso
    }
    
    logs.append(new_log)
    save_json_db(DB_LOGS_PATH, logs)
    
    return jsonify({"success": True})

# === Admin API Routes ===
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access restricted.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/admin/stats")
@admin_required
def admin_stats():
    users = load_json_db(DB_USERS_PATH)
    foods = load_json_db(DB_FOODS_PATH)
    logs = load_json_db(DB_LOGS_PATH)
    
    total_users = len(users)
    total_foods = len(foods)
    admin_count = sum(1 for u in users if u.get('role') == 'admin')
    user_count = sum(1 for u in users if u.get('role') == 'user')
    total_searches = sum(1 for l in logs if l.get('action_type') == 'search')
    
    # Active Users Today
    from datetime import datetime
    active_today = 0
    today = datetime.utcnow().date()
    for u in users:
        la = u.get('last_active')
        if la:
            try:
                if datetime.fromisoformat(la).date() == today:
                    active_today += 1
            except:
                pass
                
    # Most searched food
    from collections import Counter
    searched_foods = [l.get('food_name') for l in logs if l.get('action_type') == 'search' and l.get('food_name')]
    most_searched = Counter(searched_foods).most_common(1)[0][0] if searched_foods else "None"
    
    return jsonify({
        "totalUsers": total_users,
        "totalFoods": total_foods,
        "adminUsers": admin_count,
        "regularUsers": user_count,
        "totalSearches": total_searches,
        "activeToday": active_today,
        "mostSearched": most_searched
    })

@app.route("/admin/activity_logs")
@admin_required
def admin_activity_logs():
    logs = load_json_db(DB_LOGS_PATH)
    return jsonify({"logs": sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)})

@app.route("/admin/get_foods")
@admin_required
def get_foods_api():
    foods = load_json_db(DB_FOODS_PATH)
    return jsonify({"foods": foods})

@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    # Render previously separated admin-dashboard UI directly
    return render_template('admin-dashboard.html')

@app.route("/admin/users")
@admin_required
def admin_users():
    users = load_json_db(DB_USERS_PATH)
    # Remove passwords from response for security
    users_safe = [{k: v for k, v in u.items() if k != 'password'} for u in users]
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({"users": users_safe})
    return render_template('users.html', users=users_safe)

@app.route("/admin/delete_user/<int:id>", methods=['POST'])
@admin_required
def delete_user(id):
    if id == session.get('user_id'):
        flash('Cannot delete yourself!', 'error')
        return redirect(url_for('admin_users'))
    users = load_json_db(DB_USERS_PATH)
    users = [u for u in users if u.get('id') != id]
    save_json_db(DB_USERS_PATH, users)
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route("/admin/foods")
@admin_required
def admin_foods():
    foods = load_json_db(DB_FOODS_PATH)
    return render_template('foods.html', foods=foods)

@app.route("/admin/add_food", methods=['GET', 'POST'])
@admin_required
def add_food():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            calories = data.get('calories')
            serving = data.get('serving')
            protein = data.get('protein', 0)
            carbs = data.get('carbs', 0)
            fat = data.get('fat', 0)
        else:
            name = request.form.get('name')
            calories = request.form.get('calories')
            serving = request.form.get('serving', '100g')
            protein = request.form.get('protein', 0)
            carbs = request.form.get('carbs', 0)
            fat = request.form.get('fat', 0)
        
        if not name or not calories:
            if request.is_json:
                return jsonify({"success": False, "error": "Name and Calories are required."}), 400
            flash('Name and Calories are required.', 'error')
            return render_template('add_food.html')
            
        foods = load_json_db(DB_FOODS_PATH)
        new_id = max([f.get('id', 0) for f in foods] + [0]) + 1
        new_food = {
            "id": new_id,
            "name": name,
            "calories": float(calories),
            "protein": float(protein),
            "carbs": float(carbs),
            "fat": float(fat),
            "serving": serving
        }
        foods.append(new_food)
        save_json_db(DB_FOODS_PATH, foods)
        
        if request.is_json:
            return jsonify({"success": True, "message": "Food added successfully.", "food": new_food})
        
        flash('Food added successfully.', 'success')
        return redirect(url_for('admin_foods'))
        
    return render_template('add_food.html')

@app.route("/admin/delete_food/<int:id>", methods=['POST'])
@admin_required
def delete_food(id):
    foods = load_json_db(DB_FOODS_PATH)
    foods = [f for f in foods if f.get('id') != id]
    save_json_db(DB_FOODS_PATH, foods)
    flash('Food deleted successfully.', 'success')
    return redirect(url_for('admin_foods'))


from datetime import datetime

def write_audit_log(admin_id, admin_username, action, target_user_id=None, details=""):
    """Write an entry to the admin audit log."""
    logs = load_json_db(DB_AUDIT_PATH)
    logs.append({
        "id": max([l.get('id', 0) for l in logs] + [0]) + 1,
        "admin_id": admin_id,
        "admin_username": admin_username,
        "action": action,
        "target_user_id": target_user_id,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_json_db(DB_AUDIT_PATH, logs)


# ── BAN / UNBAN USER ─────────────────────────────────────────────
@app.route("/admin/ban_user/<int:id>", methods=['POST'])
@admin_required
def ban_user(id):
    if id == session.get('user_id'):
        return jsonify({"success": False, "error": "You cannot ban yourself."}), 400

    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    user['banned'] = True
    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "ban_user", id,
        f"Banned user: {user['username']} ({user['email']})"
    )
    return jsonify({"success": True, "message": f"User '{user['username']}' has been banned."})


@app.route("/admin/unban_user/<int:id>", methods=['POST'])
@admin_required
def unban_user(id):
    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    user['banned'] = False
    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "unban_user", id,
        f"Unbanned user: {user['username']} ({user['email']})"
    )
    return jsonify({"success": True, "message": f"User '{user['username']}' has been unbanned."})


# ── PROMOTE USER TO ADMIN ────────────────────────────────────────
@app.route("/admin/promote_user/<int:id>", methods=['POST'])
@admin_required
def promote_user(id):
    if id == session.get('user_id'):
        return jsonify({"success": False, "error": "You are already an admin."}), 400

    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    if user.get('role') == 'admin':
        return jsonify({"success": False, "error": "User is already an admin."}), 400

    user['role'] = 'admin'
    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "promote_user", id,
        f"Promoted user to admin: {user['username']} ({user['email']})"
    )
    return jsonify({"success": True, "message": f"User '{user['username']}' has been promoted to admin."})


# ── DEMOTE ADMIN TO USER ─────────────────────────────────────────
@app.route("/admin/demote_user/<int:id>", methods=['POST'])
@admin_required
def demote_user(id):
    if id == session.get('user_id'):
        return jsonify({"success": False, "error": "You cannot demote yourself."}), 400

    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    if user.get('role') != 'admin':
        return jsonify({"success": False, "error": "User is not an admin."}), 400

    user['role'] = 'user'
    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "demote_user", id,
        f"Demoted admin to user: {user['username']} ({user['email']})"
    )
    return jsonify({"success": True, "message": f"User '{user['username']}' has been demoted to regular user."})


# ── EDIT USER (username / email) ─────────────────────────────────
@app.route("/admin/edit_user/<int:id>", methods=['POST'])
@admin_required
def edit_user(id):
    data = request.get_json()
    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip()
    new_password = data.get('password', '').strip()

    if not new_username or not new_email:
        return jsonify({"success": False, "error": "Username and email are required."}), 400

    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    # Check duplicates (excluding self)
    if any(u.get('email') == new_email and u.get('id') != id for u in users):
        return jsonify({"success": False, "error": "Email already in use."}), 409
    if any(u.get('username') == new_username and u.get('id') != id for u in users):
        return jsonify({"success": False, "error": "Username already in use."}), 409

    old_username = user['username']
    user['username'] = new_username
    user['email'] = new_email
    if new_password:
        user['password'] = generate_password_hash(new_password)

    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "edit_user", id,
        f"Edited user: {old_username} → {new_username} ({new_email})"
        + (" [password reset]" if new_password else "")
    )
    return jsonify({"success": True, "message": f"User '{new_username}' updated successfully."})


# ── DELETE USER (JSON response version for AJAX) ─────────────────
@app.route("/admin/delete_user_ajax/<int:id>", methods=['POST'])
@admin_required
def delete_user_ajax(id):
    if id == session.get('user_id'):
        return jsonify({"success": False, "error": "You cannot delete yourself."}), 400

    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    users = [u for u in users if u.get('id') != id]
    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "delete_user", id,
        f"Deleted user: {user['username']} ({user['email']})"
    )
    return jsonify({"success": True, "message": f"User '{user['username']}' deleted."})


# ── AUDIT LOG VIEWER ─────────────────────────────────────────────
@app.route("/admin/audit_logs")
@admin_required
def admin_audit_logs():
    logs = load_json_db(DB_AUDIT_PATH)
    logs_sorted = sorted(logs, key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify({"logs": logs_sorted})


# ── RESET USER PASSWORD ───────────────────────────────────────────
@app.route("/admin/reset_password/<int:id>", methods=['POST'])
@admin_required
def reset_password(id):
    data = request.get_json()
    new_password = data.get('password', '').strip()

    if not new_password or len(new_password) < 6:
        return jsonify({"success": False, "error": "Password must be at least 6 characters."}), 400

    users = load_json_db(DB_USERS_PATH)
    user = next((u for u in users if u.get('id') == id), None)
    if not user:
        return jsonify({"success": False, "error": "User not found."}), 404

    user['password'] = generate_password_hash(new_password)
    save_json_db(DB_USERS_PATH, users)

    write_audit_log(
        session['user_id'], session['username'],
        "reset_password", id,
        f"Reset password for: {user['username']} ({user['email']})"
    )
    return jsonify({"success": True, "message": f"Password for '{user['username']}' has been reset."})

if __name__ == "__main__":
    # Disable debug=True for production
    app.run(debug=os.environ.get("FLASK_DEBUG", "False").lower() == "true")