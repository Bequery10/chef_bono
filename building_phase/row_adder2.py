from ai_logic import ai_utils
import json
import requests
from bs4 import BeautifulSoup
import sqlite3
import random
import time
import struct
import sqlite_vec
import threading
import os
from collections import deque


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


class RecipeProcessor:
    def __init__(self, batch_size=5):
        self.batch_size = batch_size
        self.api_key_lock = threading.Lock()
        self.db_lock = threading.Lock()
        self.lru_stack = deque()
        self.processed_count = 0
        self.processed_lock = threading.Lock()

    def _fill_lru_stack(self, limit=None):
        """Load available API keys into LRU stack"""
        index = 0
        while True:
            key = os.getenv(f"GOOGLE_API_KEY{index+1}")
            if key is None:
                break
            if limit is None or index < limit:
                self.lru_stack.append(f"GOOGLE_API_KEY{index+1}")
            index += 1
        return index - 1 if index > 0 else 0

    def _rotate_api_key(self, current_api_key_name):
        """Rotate to next available API key"""
        time.sleep(1)  # Small delay before rotation
        with self.api_key_lock:
            self.lru_stack.append(current_api_key_name)
            count = 0
            while True:
                if not self.lru_stack:
                    time.sleep(1)
                    count += 1
                    if count > 5:
                        return current_api_key_name
                    continue

                api_key_name = self.lru_stack.popleft()
                return api_key_name

    def _process_recipe_batch(self, recipes, api_key_name, results_list):
        """Process a batch of recipes with flag addition"""
        try:
            flag_adder = ai_utils.AIUtils(
                "gemini-2.5-flash-lite", api_key_name=api_key_name
            )
        except Exception as e:
            print(f"Failed to initialize with {api_key_name}, rotating...")
            new_api_key_name = self._rotate_api_key(api_key_name)
            self._process_recipe_batch(recipes, new_api_key_name, results_list)
            return

        try:
            flags = flag_adder._add_flags(recipes)
            recipes_with_flags = []

            for recipe, flag in zip(recipes, flags):
                recipe_with_flags = {**recipe, **flag}
                recipe_with_flags["categorizes"] = flag.get(
                    "main_ingredient", "Unknown"
                )

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

            flag_adder.set_embeddings()
            results_list.extend(recipes_with_flags)

            with self.processed_lock:
                self.processed_count += len(recipes_with_flags)

            with self.api_key_lock:
                self.lru_stack.append(api_key_name)

        except Exception as e:
            print(f"Error processing batch with {api_key_name}: {e}")
            new_api_key_name = self._rotate_api_key(api_key_name)
            self._process_recipe_batch(recipes, new_api_key_name, results_list)


if __name__ == "__main__":
    start_time = time.time()
    processor = RecipeProcessor(batch_size=5)

    # Initialize API key stack
    num_keys = processor._fill_lru_stack()
    print(f"Found {num_keys} API keys")

    if num_keys == 0:
        raise Exception("No API keys found. Set GOOGLE_API_KEY1, GOOGLE_API_KEY2, etc.")

    f = open("scraped_recipes.jsonl", "r")
    all_lines = f.readlines()
    f.close()
    length = len(all_lines)

    threads = []
    all_results = []
    results_lock = threading.Lock()

    # Process in batches with threading
    for i in range(0, length, processor.batch_size):
        recipes = []
        for j in range(processor.batch_size):
            if i + j >= length:
                break
            recipe_data = json.loads(all_lines[i + j])
            recipes.append(recipe_data)

        # Get available API key
        with processor.api_key_lock:
            while not processor.lru_stack:
                time.sleep(0.1)
            api_key_name = processor.lru_stack.popleft()

        # Create thread for this batch
        batch_results = []
        thread = threading.Thread(
            target=processor._process_recipe_batch,
            args=(recipes, api_key_name, batch_results),
        )
        threads.append((thread, batch_results))
        thread.start()

    # Wait for all threads to complete
    for thread, batch_results in threads:
        thread.join()
        with results_lock:
            all_results.extend(batch_results)

    # Save all results to database
    print(f"Saving {len(all_results)} recipes to database...")
    _save_to_database(all_results)

    with open("progress.txt", "w") as progress_file:
        progress_file.write(
            f"Processed {processor.processed_count} out of {length} recipes."
        )

    end_time = time.time()
    print(f"Finished adding rows to database.")
    print(f"Time taken to process: {end_time - start_time} seconds")
