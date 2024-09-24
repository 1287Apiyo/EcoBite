from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from keras.preprocessing import image
from keras.applications.mobilenet_v2 import decode_predictions
import numpy as np
import sys
import io
import json
from datetime import datetime  # Import datetime
# Force Python to use UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)
app.secret_key = 'b2f7c1f4de5c6a4d8e5c8b92f7c93f9e'

# Simulated database for users
users_db = {}
app.config['MAX_USAGE'] = 2  # Set maximum allowed uses

# Load a pre-trained MobileNetV2 model
model = MobileNetV2(weights='imagenet')

# Sample expiration dates in days
expiration_dates = {
    'banana': 7,
    'apple': 28,
    'chicken': 2,
    'milk': 7,
    'bread': 5,
    'egg': 21,
    'pizza': 3,
    'trifle': 2,
    'zucchini': 7,
    'carrot': 10,          # Added carrot
    'grapes': 5,           # Added grapes
    'potato': 14,          # Added potato
    'onion': 30,           # Added onion
    'tomato': 5,           # Added tomato
}

def predict_expiration(food_name):
    return expiration_dates.get(food_name.lower(), "Unknown food item")

# Sample recipes with URLs
recipes ={
    "banana": [
        {"name": "Banana Bread", "url": "https://www.allrecipes.com/recipe/20144/banana-banana-bread/"},
        {"name": "Banana Smoothie", "url": "https://www.allrecipes.com/recipe/220476/banana-smoothie/"}
    ],
    "apple": [
        {"name": "Apple Pie", "url": "https://www.allrecipes.com/recipe/12688/apple-pie-by-grandma-ople/"},
        {"name": "Apple Crisp", "url": "https://www.allrecipes.com/recipe/12682/apple-crisp/"}
    ],
    "chicken": [
        {"name": "Grilled Chicken", "url": "https://www.allrecipes.com/recipe/83711/grilled-chicken-breasts/"},
        {"name": "Chicken Soup", "url": "https://www.allrecipes.com/recipe/15028/chicken-soup/"}
    ],
    "milk": [
        {"name": "Pancakes", "url": "https://www.allrecipes.com/recipe/21014/good-old-fashioned-pancakes/"},
        {"name": "Milkshake", "url": "https://www.allrecipes.com/recipe/21183/milkshake/"}
    ],
    "bread": [
        {"name": "Toast", "url": "https://www.allrecipes.com/recipe/21412/bread/"},
        {"name": "Sandwich", "url": "https://www.allrecipes.com/recipe/65934/sandwich-bread/"}
    ],
    "egg": [
        {"name": "Scrambled Eggs", "url": "https://www.allrecipes.com/recipe/222609/simple-scrambled-eggs/"},
        {"name": "Omelette", "url": "https://www.allrecipes.com/recipe/222616/simple-omelet/"}
    ],
    "pizza": [
        {"name": "Pizza Casserole", "url": "https://www.allrecipes.com/recipe/83506/pizza-casserole/"},
        {"name": "Pizza Salad", "url": "https://www.allrecipes.com/recipe/228093/pizza-salad/"}
    ],
    "trifle": [
        {"name": "Fruit Trifle", "url": "https://www.allrecipes.com/recipe/75138/fruit-trifle/"},
        {"name": "Chocolate Trifle", "url": "https://www.allrecipes.com/recipe/19099/chocolate-trifle/"}
    ],
    "zucchini": [
        {"name": "Zucchini Bread", "url": "https://www.allrecipes.com/recipe/20144/zucchini-bread/"},
        {"name": "Stuffed Zucchini", "url": "https://www.allrecipes.com/recipe/21734/stuffed-zucchini/"}
    ],
    "carrot": [
        {"name": "Carrot Cake", "url": "https://www.allrecipes.com/recipe/17481/carrot-cake/"},
        {"name": "Carrot Soup", "url": "https://www.allrecipes.com/recipe/10336/carrot-soup/"}
    ],
    "grapes": [
        {"name": "Grape Salad", "url": "https://www.allrecipes.com/recipe/216134/grape-salad/"},
        {"name": "Frozen Grapes", "url": "https://www.allrecipes.com/recipe/222121/frozen-grapes/"}
    ],
    "potato": [
        {"name": "Mashed Potatoes", "url": "https://www.allrecipes.com/recipe/23518/mashed-potatoes/"},
        {"name": "Potato Wedges", "url": "https://www.allrecipes.com/recipe/15100/potato-wedges/"}
    ],
    "onion": [
        {"name": "French Onion Soup", "url": "https://www.allrecipes.com/recipe/21735/french-onion-soup/"},
        {"name": "Caramelized Onions", "url": "https://www.allrecipes.com/recipe/24443/caramelized-onions/"}
    ],
    "tomato": [
        {"name": "Tomato Sauce", "url": "https://www.allrecipes.com/recipe/21014/tomato-sauce/"},
        {"name": "Caprese Salad", "url": "https://www.allrecipes.com/recipe/23969/caprese-salad/"}
    ]
}



def suggest_recipes(food_name):
    return recipes.get(food_name.lower(), [])

# Sample nutritional information
nutritional_info = {
    'banana': {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3},
    'apple': {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2},
    'chicken': {"calories": 239, "protein": 27, "carbs": 0, "fat": 14},
    'milk': {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1},
    'bread': {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2},
    'egg': {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11},
    'pizza': {"calories": 285, "protein": 12, "carbs": 36, "fat": 10},
    'trifle': {"calories": 120, "protein": 2, "carbs": 20, "fat": 4},
    'zucchini': {"calories": 17, "protein": 1.2, "carbs": 3.1, "fat": 0.2},
    'carrot': {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2},
    'grapes': {"calories": 69, "protein": 0.7, "carbs": 18, "fat": 0.2},
    'potato': {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1},
    'onion': {"calories": 40, "protein": 1.1, "carbs": 9.3, "fat": 0.1},
    'tomato': {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2},
}

def get_nutritional_info(food_name):
    return nutritional_info.get(food_name.lower(), {"calories": "N/A", "protein": "N/A", "carbs": "N/A", "fat": "N/A"})
@app.route('/')
def home():
    if 'username' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    # Check if the user has used the system more than allowed
    if 'usage_count' in session and session['usage_count'] >= app.config['MAX_USAGE']:
        flash('You must register to continue using the system.', 'danger')
        return redirect(url_for('register'))
    
    # Increment usage count
    session['usage_count'] = session.get('usage_count', 0) + 1

    # Retrieve user-specific predictions, recent uploads, or favorite recipes from session
    user_predictions = session.get('predictions', [])
    favorite_recipes = session.get('favorite_recipes', [])


    session_predictions = session.get('predictions', [])
    displayed_predictions = session_predictions[:6]  # Limit to first 6 predictions


    return render_template('index.html', predictions=user_predictions, favorite_recipes=favorite_recipes)


@app.route('/all_predictions')
def all_predictions():
    if 'username' not in session:
        return redirect('/login')  # Redirect to login if not logged in

    session_predictions = session.get('predictions', [])

    return render_template('all_predictions.html', predictions=session_predictions)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users_db:
            flash('Username already exists. Please choose a different one.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            users_db[username] = hashed_password
            flash('Your account has been created! You can now log in.', 'success')
            session['usage_count'] = 0
            return redirect(url_for('login'))  # Redirect to login

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users_db and check_password_hash(users_db[username], password):
            session['username'] = username
            flash('You have been logged in!', 'success')
            session['usage_count'] = 0
            return redirect(url_for('home'))  # Make sure this matches the function name
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')

from flask import session, redirect, url_for, flash

@app.route('/logout')
def logout():
    # Remove user from the session
    session.pop('username', None)
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))  # Redirect to the login page after logout

@app.route('/save_recipe', methods=['POST'])
def save_recipe():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    recipe_name = request.form.get('recipe_name')
    recipe_url = request.form.get('recipe_url')

    # Get current saved recipes and append new one
    favorite_recipes = session.get('favorite_recipes', [])
    favorite_recipes.append({"name": recipe_name, "url": recipe_url})
    session['favorite_recipes'] = favorite_recipes

    flash(f"Recipe '{recipe_name}' saved successfully!", 'success')
    return redirect(url_for('home'))
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    # Get items nearing expiration
    user_predictions = session.get('predictions', [])
    
    # Debugging output
    print(f"User Predictions: {user_predictions}")  # Print user predictions for debugging
    
    # Ensure expiration days are integers for comparison
    nearing_expiration = [item for item in user_predictions if isinstance(item['expiration'], int) and item['expiration'] <= 3]  # 3 days threshold

    return render_template('dashboard.html', nearing_expiration=nearing_expiration)


@app.route('/log_waste', methods=['POST'])
def log_waste():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    waste_item = request.form.get('waste_item')
    # Here you could save this to a database or session
    flash(f"Logged {waste_item} as wasted.", 'info')
    return redirect(url_for('dashboard'))

@app.route('/recipes')
def recipes_page():
    recipes = [
      
    {
        "name": "Vegetable Stir Fry",
        "description": "A quick and easy stir fry with seasonal vegetables.",
        "ingredients": "Bell peppers, carrots, broccoli, soy sauce, garlic.",
        "prep_time": "15 minutes",
        "instructions": "1. Chop the vegetables. 2. Heat oil in a pan. 3. Stir-fry the vegetables for 5-7 minutes. 4. Add soy sauce and garlic, cook for another 2 minutes."
    },
    {
        "name": "Banana Bread",
        "description": "A delicious way to use overripe bananas.",
        "ingredients": "Ripe bananas, flour, sugar, eggs, butter, baking soda.",
        "prep_time": "10 minutes",
        "instructions": "1. Preheat oven to 350°F. 2. Mash bananas. 3. Mix all ingredients and pour into a loaf pan. 4. Bake for 50-60 minutes."
    },
    {
        "name": "Spaghetti Aglio e Olio",
        "description": "A simple pasta dish with garlic and olive oil.",
        "ingredients": "Spaghetti, garlic, olive oil, red pepper flakes, parsley.",
        "prep_time": "20 minutes",
        "instructions": "1. Cook spaghetti. 2. In a pan, heat olive oil and sauté garlic. 3. Add cooked spaghetti and red pepper flakes. 4. Toss and garnish with parsley."
    },
    {
        "name": "Chickpea Salad",
        "description": "A refreshing salad packed with protein.",
        "ingredients": "Chickpeas, cucumber, cherry tomatoes, red onion, lemon juice, olive oil.",
        "prep_time": "10 minutes",
        "instructions": "1. Rinse chickpeas. 2. Chop vegetables. 3. Mix all ingredients and serve."
    },
    {
        "name": "Chocolate Mug Cake",
        "description": "A quick and easy dessert made in a mug.",
        "ingredients": "Flour, sugar, cocoa powder, baking powder, milk, oil, vanilla.",
        "prep_time": "5 minutes",
        "instructions": "1. Mix dry ingredients in a mug. 2. Add wet ingredients and stir. 3. Microwave for 1-2 minutes."
    },
    {
        "name": "Caprese Salad",
        "description": "A fresh salad with mozzarella, tomatoes, and basil.",
        "ingredients": "Fresh mozzarella, tomatoes, basil, olive oil, balsamic vinegar.",
        "prep_time": "10 minutes",
        "instructions": "1. Slice mozzarella and tomatoes. 2. Layer with basil. 3. Drizzle with olive oil and balsamic vinegar."
    },
    {
        "name": "Pancakes",
        "description": "Fluffy pancakes for breakfast or brunch.",
        "ingredients": "Flour, milk, eggs, baking powder, sugar, butter.",
        "prep_time": "15 minutes",
        "instructions": "1. Mix dry ingredients. 2. Add wet ingredients. 3. Cook on a griddle until golden brown."
    }
]

    current_year = datetime.now().year
    return render_template('recipes.html', recipes=recipes, current_year=current_year)

@app.route('/tips')
def tips():
    # Display tips on reducing food waste
    waste_tips = [
        "Plan your meals to avoid overbuying.",
        "Store food properly to maximize freshness.",
        "Use leftovers creatively in new meals.",
        "Keep track of expiration dates to use food in time.",
        "Share excess food with friends or neighbors."
    ]
    return render_template('tips.html', tips=waste_tips)
@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return jsonify({"error": "User not logged in"}), 401

    img_file = request.files['image']
    img_path = "uploaded_image.jpg"
    img_file.save(img_path)

    # Load and preprocess the image
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    # Perform prediction
    preds = model.predict(img_array)
    results = decode_predictions(preds, top=3)[0]

    predictions = [{'name': res[1], 'probability': float(res[2])} for res in results]

    # Store predictions in session
    session_predictions = session.get('predictions', [])
    for pred in predictions:
        food_name = pred['name']
        expiration_days = predict_expiration(food_name)
        suggested_recipes = suggest_recipes(food_name)
        nutrition_info = get_nutritional_info(food_name)

        # Ensure expiration days is stored as an integer
        try:
            if isinstance(expiration_days, (int, float)):  # Check if it's a number
                pred['expiration'] = int(expiration_days)  # Cast to integer
            else:
                raise ValueError("Expiration days is not a valid number")
        except ValueError:
            pred['expiration'] = 0  # Assign a default value for invalid cases
        
        pred['recipes'] = suggested_recipes
        pred['nutrition'] = nutrition_info
        
        # Debugging output
        print(f"Prediction: {pred}")  # Print prediction for debugging
        
        session_predictions.append(pred)

    # Update session with new predictions
    session['predictions'] = session_predictions
    
    return jsonify(predictions)  # Return predictions as JSON


if __name__ == '__main__':
    app.run(debug=True)