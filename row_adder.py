import ai_utils
import json
import requests
from bs4 import BeautifulSoup
import sqlite3


def _save_to_database(recipes):
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ingredients TEXT NOT NULL,
            preparation TEXT NOT NULL,
            meal_type INTEGER CHECK (meal_type >= 1 AND meal_type <= 3),
            main_ingredient TEXT,
            vegetarian BOOLEAN DEFAULT FALSE,
            vegan BOOLEAN DEFAULT FALSE,
            gluten_free BOOLEAN DEFAULT FALSE,
            dairy_free BOOLEAN DEFAULT FALSE,
            nut_free BOOLEAN DEFAULT FALSE,
            high_fiber BOOLEAN DEFAULT FALSE,
            weight_loss_diet BOOLEAN DEFAULT FALSE,
            muscle_gain_bulking BOOLEAN DEFAULT FALSE,
            balanced_healthy BOOLEAN DEFAULT FALSE,
            carb_score FLOAT DEFAULT 0,
            protein_score FLOAT DEFAULT 0,
            fat_score FLOAT DEFAULT 0,
            calorie_score FLOAT DEFAULT 0,
            sugar_score FLOAT DEFAULT 0
        )
    """
    )
    for recipe in recipes:
        cursor.execute(
            """
            INSERT INTO recipes (
                name, ingredients, preparation,
                meal_type, main_ingredient,
                vegetarian, vegan, gluten_free, dairy_free, nut_free,
                high_fiber, weight_loss_diet, muscle_gain_bulking, balanced_healthy,
                carb_score, protein_score, fat_score, calorie_score, sugar_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                recipe["name"],
                recipe["ingredients"],
                recipe["preparation"],
                recipe["meal_type"],
                recipe["main_ingredient"],
                recipe["vegetarian"],
                recipe["vegan"],
                recipe["gluten_free"],
                recipe["dairy_free"],
                recipe["nut_free"],
                recipe["high_fiber"],
                recipe["weight_loss_diet"],
                recipe["muscle_gain_bulking"],
                recipe["balanced_healthy"],
                recipe["carb_score"],
                recipe["protein_score"],
                recipe["fat_score"],
                recipe["calorie_score"],
                recipe["sugar_score"],
            ),
        )
    conn.commit()
    conn.close()
    print("Recipes saved to database successfully.")


def _scrap_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    name_tag = soup.find("p", class_="H2")
    recipe_name = name_tag.get_text(strip=True) if name_tag else None

    # Extract ingredients
    ingredients_table = soup.find("span", string="ingredients")
    ingredients = None
    if ingredients_table:
        ingredients_p = ingredients_table.find_next("p", class_="H1")
        ingredients = (
            ingredients_p.get_text(separator="\n", strip=True)
            if ingredients_p
            else None
        )

    # Extract preparation
    prep_table = soup.find("span", string="preparation")
    preparation = None
    if prep_table:
        prep_p = prep_table.find_next("p", class_="H1")
        preparation = prep_p.get_text(separator="\n", strip=True) if prep_p else None

    return {"name": recipe_name, "ingredients": ingredients, "preparation": preparation}


if __name__ == "__main__":

    recipes = []
    flag_adder = ai_utils.AIUtils("gemini-2.0-flash")

    for i in range(1, 12):
        if i == 2:
            continue
        response = requests.get(f"https://cookbooks.com/Recipe-Details.aspx?id={i}")
        if response.status_code != 200:
            print("Failed to retrieve the webpage.")
            exit()

        recipe_data = _scrap_html(response.text)
        recipes.append(recipe_data)

    # Add flags to each recipe dict
    flags = flag_adder._add_flags(recipes)
    recipes_with_flags = []
    for recipe, flag in zip(recipes, flags):
        recipe_with_flags = {**recipe, **flag}
        # Ensure all required fields are present and not None
        required_fields = [
            "name",
            "ingredients",
            "preparation",
            "meal_type",
            "main_ingredient",
            "vegetarian",
            "vegan",
            "gluten_free",
            "dairy_free",
            "nut_free",
            "high_fiber",
            "weight_loss_diet",
            "muscle_gain_bulking",
            "balanced_healthy",
            "carb_score",
            "protein_score",
            "fat_score",
            "calorie_score",
            "sugar_score",
        ]
        if all(
            field in recipe_with_flags and recipe_with_flags[field] is not None
            for field in required_fields
        ):
            recipes_with_flags.append(recipe_with_flags)

    _save_to_database(recipes_with_flags)

    recipes = None
    flags = None
