import ai_utils
import json
import requests
from bs4 import BeautifulSoup
import sqlite3
import random
import time
import struct
import sqlite_vec


def serialize_f32(vector):
    """Serializes a list of floats into a compact 'raw bytes' format."""
    return struct.pack("%sf" % len(vector), *vector)


def _save_to_database(recipes):
    conn = sqlite3.connect("recipes.db")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    cursor = conn.cursor()
    for recipe in recipes:
        # Serialize embedding if it's a list
        embedding = recipe["embedding"]
        if isinstance(embedding, list):
            embedding = serialize_f32(embedding)
        cursor.execute(
            """
            INSERT INTO recipes (
                name, ingredients, preparation,
                embedding, meal_type, main_ingredient, nationality,
                vegetarian, vegan, gluten_free, dairy_free, nut_free,
                high_fiber, weight_loss_diet, muscle_gain_bulking, balanced_healthy,
                carb_score, protein_score, fat_score, calorie_score, sugar_score,
                preparation_time_score, preparation_difficulty_score, meal_class
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                recipe["name"],
                recipe["ingredients"],
                recipe["preparation"],
                embedding,
                recipe["meal_type"],
                recipe["main_ingredient"],
                recipe["nationality"],
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
                recipe["preparation_time_score"],
                recipe["preparation_difficulty_score"],
                recipe["meal_class"],
            ),
        )
    conn.commit()
    conn.close()


def _scrap_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    name_tag = soup.find("p", class_="H2")
    recipe_name = name_tag.get_text(strip=True) if name_tag else None

    print(f"Scraping recipe: {recipe_name}")
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


def _recipe_categorizer(recipes):
    pass


if __name__ == "__main__":

    recipes = []
    flag_adder = ai_utils.AIUtils("gemini-2.5-flash-lite")
    start_time = time.time()
    for i in range(3):

        response = requests.get(
            f"https://cookbooks.com/Recipe-Details.aspx?id={random.randint(1,1000000)}"
        )
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
        recipe_with_flags["categorizes"] = flag.get("main_ingredient", "Unknown")
        required_fields = [
            "name",
            "ingredients",
            "preparation",
            "embedding",
            "meal_type",
            "main_ingredient",
            "nationality",
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
            "preparation_time_score",
            "preparation_difficulty_score",
            "meal_class",
        ]
        if all(
            field in recipe_with_flags and recipe_with_flags[field] is not None
            for field in required_fields
        ):
            recipes_with_flags.append(recipe_with_flags)

    _save_to_database(recipes_with_flags)
    flag_adder.set_embeddings()
    print("Finished adding rows to database.")
    end_time = time.time()
    print(f"Time taken to process: {end_time - start_time} seconds")
    recipes = None
    flags = None
