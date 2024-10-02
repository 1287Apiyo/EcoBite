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

def is_food_label(label):
    """Check if the label is related to food"""
    return any(food in label for food in food_labels)

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
    'ugali': 3,                 # Ugali (cornmeal)
    'collard greens': 3,        # Sukuma Wiki (collard greens)
    'githeri': 5,               # Githeri (maize and beans mix)
    'grilled meat': 2,          # Nyama Choma (grilled meat)
    'mandazi': 3,               # Mandazi (fried dough)
    'chapati': 3,               # Chapati (flatbread)
    'green grams': 4,           # Ndengu (green grams)
    'small dried fish': 7,      # Omena (small dried fish)
    'plantain': 7,              # Matoke (green bananas)
    'mashed potatoes with greens': 4,  # Mokimo (mashed potatoes with greens)
    'pilau': 2,                 # Pilau (spiced rice and meat)
    'chicken': 2,               # Kuku (chicken)
    'tilapia': 2,               # Tilapia fish (fresh)
    'mukimo': 3,                # Mukimo (mashed peas, potatoes, and greens)
    'beef stew': 3,             # Beef stew
    'dry maize flour': 30,      # Ugali mix (dry flour)
    'arrowroot': 5,             # Nduma (arrowroot)
    'dry maize': 30,            # Mahindi (dry maize)
    'millet porridge': 3,       # Wimbi porridge
    'cassava': 5,               # Muhogo (cassava)
    'tripe': 1,                 # Matumbo (tripe)
    'traditional chicken': 2,   # Kienyeji chicken (traditional chicken)
    'traditional greens': 3,    # Mboga Kienyeji (traditional greens)
    'fish stew': 2,             # Fish stew
    'bean stew': 4,             # Bean stew
    'millet ugali': 5,          # Ugali made from millet flour
    'arrowroots': 7,            # Nduma (arrowroots)
    'potatoes': 14,             # Waru (potatoes)
    'samosa': 2,                # Samosa (fried meat/veg pastry)
    'potato fritters': 2,       # Bhajia (spiced potato fritters)
    'Kenyan sausage': 1,        # Mutura (Kenyan sausage)
    'mashed peas and corn': 3,  # Irio (mashed peas, potatoes, and corn)
    'coconut rice': 2,          # Coconut rice
    'pigeon peas': 4,           # Mbaazi (pigeon peas)
    'cowpeas leaves': 3,        # Kunde (cowpeas leaves)
    'lamb stew': 3,             # Lamb stew
    'lentil stew': 4,  
    'mashed_potato':3,         # Kamande (lentil stew)
    
    # Adding fruits at the end
    'banana': 7,
    'apple': 28,
    'mango': 5,
    'pineapple': 5,
    'avocado': 4,
    'papaya': 4,
    'watermelon': 7,
    'passion fruit': 7,
    'guava': 5,
    'oranges': 14,
    'lemon': 30,
    'tangerine': 14,
    'kiwi': 10,
}


def predict_expiration(food_name):
    return expiration_dates.get(food_name.lower(), "Unknown food item")

# Sample recipes with URLs
recipes ={
    "banana": [
        {"name": "Banana Bread", "url": "https://www.allrecipes.com"},
        {"name": "Banana Smoothie", "url": "https://www.allrecipes.com"}
    ],
    "apple": [
        {"name": "Apple Pie", "url": "https://www.allrecipes.com"},
        {"name": "Apple Crisp", "url": "https://www.allrecipes.com"}
    ],
    "chicken": [
        {"name": "Grilled Chicken", "url": "https://www.allrecipes.com"},
        {"name": "Chicken Soup", "url": "https://www.allrecipes.com"}
    ],
    "milk": [
        {"name": "Pancakes", "url": "https://www.allrecipes.com"},
        {"name": "Milkshake", "url": "https://www.allrecipes.com"}
    ],
    "bread": [
        {"name": "Toast", "url": "https://www.allrecipes.com"},
        {"name": "Sandwich", "url": "https://www.allrecipes.com"}
    ],
    "egg": [
        {"name": "Scrambled Eggs", "url": "https://www.allrecipes.com"},
        {"name": "Omelette", "url": "https://www.allrecipes.com"}
    ],
    "pizza": [
        {"name": "Pizza Casserole", "url": "https://www.allrecipes.com"},
        {"name": "Pizza Salad", "url": "https://www.allrecipes.com"}
    ],
    "trifle": [
        {"name": "Fruit Trifle", "url": "https://www.allrecipes.com"},
        {"name": "Chocolate Trifle", "url": "https://www.allrecipes.com"}
    ],
    "zucchini": [
        {"name": "Zucchini Bread", "url": "https://www.allrecipes.com"},
        {"name": "Stuffed Zucchini", "url": "https://www.allrecipes.com"}
    ],
    "carrot": [
        {"name": "Carrot Cake", "url": "https://www.allrecipes.com"},
        {"name": "Carrot Soup", "url": "https://www.allrecipes.com"}
    ],
    "grapes": [
        {"name": "Grape Salad", "url": "https://www.allrecipes.com"},
        {"name": "Frozen Grapes", "url": "https://www.allrecipes.com"}
    ],
    "potato": [
        {"name": "Mashed Potatoes", "url": "https://www.allrecipes.com"},
        {"name": "Potato Wedges", "url": "https://www.allrecipes.com"}
    ],
    "onion": [
        {"name": "French Onion Soup", "url": "https://www.allrecipes.com"},
        {"name": "Caramelized Onions", "url": "https://www.allrecipes.com"}
    ],
    "tomato": [
        {"name": "Tomato Sauce", "url": "https://www.allrecipes.com"},
        {"name": "Caprese Salad", "url": "https://www.allrecipes.com"}
    ],
    "ugali": [
        {"name": "Traditional Ugali", "url": "https://www.allrecipes.com"},
        {"name": "Ugali with Sukuma Wiki", "url": "https://www.allrecipes.com"}
    ],
    "collard greens": [
        {"name": "Sukuma Wiki Recipe", "url": "https://www.allrecipes.com"},
        {"name": "Collard Greens with Tomatoes", "url": "https://www.allrecipes.com"}
    ],
    "githeri": [
        {"name": "Githeri Recipe", "url": "https://www.allrecipes.com"},
        {"name": "Githeri with Avocado", "url": "https://www.allrecipes.com"}
    ],
    "grilled meat": [
        {"name": "Nyama Choma", "url": "https://www.allrecipes.com"},
        {"name": "Nyama Choma with Kachumbari", "url": "https://www.allrecipes.com"}
    ],
    "mandazi": [
        {"name": "Soft Mandazi", "url": "https://www.allrecipes.com"},
        {"name": "Coconut Mandazi", "url": "https://www.allrecipes.com"}
    ],
    "chapati": [
        {"name": "Soft Chapati", "url": "https://www.allrecipes.com"},
        {"name": "Layered Chapati", "url": "https://www.allrecipes.com"}
    ],
    "green grams": [
        {"name": "Ndengu Stew", "url": "https://www.allrecipes.com"},
        {"name": "Coconut Ndengu", "url": "https://www.allrecipes.com"}
    ],
    "small dried fish": [
        {"name": "Fried Omena", "url": "https://www.allrecipes.com"},
        {"name": "Omena Stew", "url": "https://www.allrecipes.com"}
    ],
    "plantain": [
        {"name": "Matoke Stew", "url": "https://www.allrecipes.com"},
        {"name": "Fried Matoke", "url": "https://www.allrecipes.com"}
    ],
    "mashed potatoes with greens": [
        {"name": "Traditional Mokimo", "url": "https://www.allrecipes.com"},
        {"name": "Mokimo with Githeri", "url": "https://www.allrecipes.com"}
    ],
    "tilapia": [
        {"name": "Fried Tilapia", "url": "https://www.allrecipes.com"},
        {"name": "Tilapia Stew", "url": "https://www.allrecipes.com"}
    ],
    "beef stew": [
        {"name": "Kenyan Beef Stew", "url": "https://www.allrecipes.com"},
        {"name": "Beef Stew with Ugali", "url": "https://www.allrecipes.com"}
    ],
    "arrowroot": [
        {"name": "Boiled Nduma", "url": "https://www.allrecipes.com"},
        {"name": "Fried Nduma", "url": "https://www.allrecipes.com"}
    ],
    "bean stew": [
        {"name": "Kenyan Bean Stew", "url": "https://www.allrecipes.com"},
        {"name": "Coconut Bean Stew", "url": "https://www.allrecipes.com"}
    ],
    "potato fritters": [
        {"name": "Bhajia Recipe", "url": "https://www.allrecipes.com"},
        {"name": "Bhajia with Chutney", "url": "https://www.allrecipes.com"}
    ],
    "Kenyan sausage": [
        {"name": "Mutura Recipe", "url": "https://www.allrecipes.com"},
        {"name": "Spicy Mutura", "url": "https://www.allrecipes.com"}
    ],
    "coconut rice": [
        {"name": "Kenyan Coconut Rice", "url": "https://www.allrecipes.com"},
        {"name": "Coconut Rice with Chicken", "url": "https://www.allrecipes.com"}
    ],
    
    # Adding fruits at the end
    "banana": [
        {"name": "Banana Bread", "url": "https://www.allrecipes.com"},
        {"name": "Banana Smoothie", "url": "https://www.allrecipes.com"}
    ],
    "mango": [
        {"name": "Mango Salad", "url": "https://www.allrecipes.com"},
        {"name": "Mango Chutney", "url": "https://www.allrecipes.com"}
    ],
    "avocado": [
        {"name": "Avocado Salad", "url": "https://www.allrecipes.com"},
        {"name": "Guacamole", "url": "https://www.allrecipes.com"}
    ],
    "papaya": [
        {"name": "Papaya Salad", "url": "https://www.allrecipes.com"},
        {"name": "Papaya Smoothie", "url": "https://www.allrecipes.com"}
    ],
}



def suggest_recipes(food_name):
    return recipes.get(food_name.lower(), [])

# Sample nutritional information
nutritional_info = {
    'mashed_potato': {"calories": 125, "protein": 3, "carbs": 30, "fat": 2},

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
    'ugali': {"calories": 110, "protein": 2.6, "carbs": 25, "fat": 0.5},
    'collard greens': {"calories": 33, "protein": 2.9, "carbs": 6.1, "fat": 0.7},
    'githeri': {"calories": 190, "protein": 10, "carbs": 30, "fat": 5},
    'grilled meat': {"calories": 250, "protein": 20, "carbs": 0, "fat": 15},
    'mandazi': {"calories": 200, "protein": 4, "carbs": 30, "fat": 8},
    'chapati': {"calories": 180, "protein": 4, "carbs": 32, "fat": 5},
    'green grams': {"calories": 105, "protein": 7.1, "carbs": 18.6, "fat": 0.3},
    'small dried fish': {"calories": 150, "protein": 30, "carbs": 0, "fat": 5},
    'plantain': {"calories": 90, "protein": 1, "carbs": 23, "fat": 0.1},
    'mashed potatoes with greens': {"calories": 125, "protein": 3, "carbs": 30, "fat": 2},
    'tilapia': {"calories": 128, "protein": 26, "carbs": 0, "fat": 2.7},
    'beef stew': {"calories": 250, "protein": 28, "carbs": 10, "fat": 12},
    'arrowroot': {"calories": 98, "protein": 2, "carbs": 20, "fat": 0.1},
    'bean stew': {"calories": 200, "protein": 10, "carbs": 35, "fat": 5},
    'potato fritters': {"calories": 140, "protein": 4, "carbs": 22, "fat": 6},
    'Kenyan sausage': {"calories": 280, "protein": 14, "carbs": 5, "fat": 22},
    'coconut rice': {"calories": 190, "protein": 3, "carbs": 35, "fat": 4},
    
    # Adding fruits at the end
    'banana': {"calories": 90, "protein": 1, "carbs": 23, "fat": 0.3},
    'mango': {"calories": 60, "protein": 0.8, "carbs": 15, "fat": 0.4},
    'avocado': {"calories": 160, "protein": 2, "carbs": 9, "fat": 15},
    'papaya': {"calories": 55, "protein": 0.5, "carbs": 14, "fat": 0.1},

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
            pred['expiration'] = 0 
        
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