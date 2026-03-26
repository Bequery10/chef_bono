from ai_logic import ai_utils
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
        # Remove embedding from the insert into recipes
        cursor.execute(
            """
            INSERT INTO recipes (
                name, ingredients, preparation,
                meal_type, main_ingredient, nationality,
                vegetarian, vegan, gluten_free, dairy_free, nut_free,
                high_fiber, weight_loss_diet, muscle_gain_bulking, balanced_healthy,
                carb_score, protein_score, fat_score, calorie_score, sugar_score, spice_level_score,
                preparation_time_score, preparation_difficulty_score, meal_class
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                recipe["name"],
                recipe["ingredients"],
                recipe["preparation"],
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
                recipe["spice_level_score"],
                recipe["preparation_time_score"],
                recipe["preparation_difficulty_score"],
                recipe["meal_class"],
            ),
        )
        # Get the id of the inserted recipe
        recipe_id = cursor.lastrowid
        # Insert embedding into recipes_vec
        embedding = recipe["embedding"]
        if isinstance(embedding, list):
            embedding = serialize_f32(embedding)
        cursor.execute(
            "INSERT INTO recipes_vec(rowid, embedding) VALUES (?, ?)",
            (recipe_id, embedding),
        )
    conn.commit()
    conn.close()


def _recipe_categorizer(recipes):
    pass


if __name__ == "__main__":

    flag_adder = ai_utils.AIUtils("gemini-2.5-flash-lite")
    start_time = time.time()

    f = open("scraped_recipes.jsonl", "r")
    count = 0
    length = len(f.readlines())
    f.seek(0)  # Reset file pointer to the beginning after counting lines
    for i in range(0, length, 5):
        recipes = []
        for j in range(5):
            recipe_data = json.loads(f.readline())
            print(recipe_data["name"])
            print(recipe_data["ingredients"])
            print(recipe_data["preparation"])
            recipes.append(recipe_data)
            count += 1

        # Add flags to each recipe dict
        flags = flag_adder._add_flags(recipes)
        recipes_with_flags = []

        with open("progress.txt", "w") as progress_file:
            progress_file.write(f"Processed {count} out of {length} recipes.")

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
                "spice_level_score",
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
