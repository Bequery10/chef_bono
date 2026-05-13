DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS recipes_vec;

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    ingredients TEXT NOT NULL,
    preparation TEXT NOT NULL,
    meal_type  TEXT CHECK (
        meal_type IN (
            'Breakfast',
            'Lunch',
            'Dinner'
        )
    ),
    main_ingredient VARCHAR(255),
    nationality VARCHAR(100),
    vegetarian BOOLEAN DEFAULT FALSE,
    vegan BOOLEAN DEFAULT FALSE,
    gluten_free BOOLEAN DEFAULT FALSE,
    dairy_free BOOLEAN DEFAULT FALSE,
    nut_free BOOLEAN DEFAULT FALSE,
    high_fiber BOOLEAN DEFAULT FALSE,
    weight_loss_diet BOOLEAN DEFAULT FALSE,
    muscle_gain_bulking BOOLEAN DEFAULT FALSE,
    balanced_healthy BOOLEAN DEFAULT FALSE,
    carb_score FLOAT DEFAULT 0 CHECK (carb_score <=1),
    protein_score FLOAT DEFAULT 0 CHECK (protein_score <=1),
    fat_score FLOAT DEFAULT 0 CHECK (fat_score <=1),
    calorie_score FLOAT DEFAULT 0 CHECK (calorie_score <=1),
    sugar_score FLOAT DEFAULT 0 CHECK (sugar_score <=1),
    spice_level_score FLOAT DEFAULT 0 CHECK (spice_level_score <=1),
    preparation_time_score FLOAT DEFAULT 0 CHECK (preparation_time_score <=1),
    preparation_difficulty_score FLOAT DEFAULT 0 CHECK (preparation_difficulty_score <=1),
    meal_class TEXT CHECK (
        meal_class IN (
            'Pasta',
            'Pizza',
            'Rice dish',
            'Noodle',
            'Burger',
            'Sandwich',
            'Wrap',
            'Taco',
            'Kebab',
            'Steak',
            'Grilled meat',
            'Fried chicken',
            'Seafood',
            'Curry',
            'Stew',
            'Casserole',
            'Salad',
            'Soup',
            'Bowl',
            'Fries',
            'Potato dish',
            'Bread',
            'Egg dish',
            'Pancake / waffle',
            'Dumplings',
            'Rolls',
            'Finger food',
            'Pastry',
            'Cake',
            'Cookie',
            'Ice cream',
            'Syrup dessert',
            'Coffee',
            'Tea',
            'Soft drink',
            'Smoothie / shake'
        )
    )
);

CREATE VIRTUAL TABLE recipes_vec USING vec0(embedding float[768]);