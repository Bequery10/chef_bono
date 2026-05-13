import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_logic import ai_utils
import json
import requests
from bs4 import BeautifulSoup
import sqlite3
import random
import time
import struct
import sqlite_vec
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Lock for thread-safe database writes
db_lock = Lock()

# Progress tracking file
PROGRESS_FILE = "database_utils/progress.txt"


def serialize_f32(vector):
    """Serializes a list of floats into a compact 'raw bytes' format."""
    return struct.pack("%sf" % len(vector), *vector)


def get_last_processed_line():
    """Load last processed line index from progress file"""
    try:
        with open(PROGRESS_FILE, "r") as f:
            data = f.read().strip().split("\n")
            for line in data:
                if line.startswith("last_line:"):
                    return int(line.split(":")[1])
    except (FileNotFoundError, ValueError):
        pass
    return 0


def update_progress(last_line, count, total):
    """Update progress file with current state"""
    with open(PROGRESS_FILE, "w") as f:
        f.write(f"last_line:{last_line}\n")
        f.write(f"processed:{count}\n")
        f.write(f"total:{total}\n")


def _save_to_database(recipes_with_ids):
    """Thread-safe database insertion with explicit IDs"""
    with db_lock:
        conn = sqlite3.connect("database_utils/recipes.db")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        cursor = conn.cursor()
        for recipe_id, recipe in recipes_with_ids:
            cursor.execute(
                """
                INSERT INTO recipes (
                    id, name, ingredients, preparation,
                    meal_type, main_ingredient, nationality,
                    vegetarian, vegan, gluten_free, dairy_free, nut_free,
                    high_fiber, weight_loss_diet, muscle_gain_bulking, balanced_healthy,
                    carb_score, protein_score, fat_score, calorie_score, sugar_score, spice_level_score,
                    preparation_time_score, preparation_difficulty_score, meal_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    recipe_id,
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
            embedding = recipe["embedding"]
            if isinstance(embedding, list):
                embedding = serialize_f32(embedding)
            cursor.execute(
                "INSERT INTO recipes_vec(rowid, embedding) VALUES (?, ?)",
                (recipe_id, embedding),
            )
        conn.commit()
        conn.close()


def process_batch(recipes_with_line_indices, key_index, flag_adder=None):
    """Process a batch of recipes with a specific API key index"""
    if flag_adder is None:
        flag_adder = ai_utils.AIUtils("gemini-3.1-flash-lite")

    # Extract recipes and line indices
    recipes = [r[1] for r in recipes_with_line_indices]
    line_indices = [r[0] for r in recipes_with_line_indices]

    # Add flags using key_index parameter
    flags = flag_adder._add_flags(recipes, key_index)
    recipes_with_flags = []

    for line_idx, recipe, flag in zip(line_indices, recipes, flags):
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
            recipes_with_flags.append((line_idx, recipe_with_flags))

    return recipes_with_flags


if __name__ == "__main__":
    start_time = time.time()

    f = open("building_phase/scraped_recipes.jsonl", "r")

    # Get total number of lines
    total_lines = len(f.readlines())
    f.seek(0)

    # Get last processed line and start from next
    last_processed_line = get_last_processed_line()
    current_line = last_processed_line  # Start from last processed index

    # Skip to resume point
    for _ in range(current_line):
        f.readline()

    # Create flag_adder for interrupt handling
    flag_adder = ai_utils.AIUtils("gemini-3.1-flash-lite")
    current_key_index = 0
    count = 0

    try:
        # Use ThreadPoolExecutor with 5 workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures_dict = {}  # Map future to batch index
            batch_index = 0

            print(
                f"Starting from line {current_line} out of {total_lines}. Total recipes processed so far: {count}"
            )

            # Submit initial batches to fill the thread pool
            while current_line < total_lines and len(futures_dict) < 5:
                # time.sleep(1)
                recipes_with_indices = []

                # Read batch of 5 recipes
                for j in range(5):
                    line = f.readline()
                    if not line.strip():
                        break

                    recipe_data = json.loads(line)
                    recipes_with_indices.append((current_line, recipe_data))
                    count += 1
                    current_line += 1

                if recipes_with_indices:
                    # Round-robin key assignment by index
                    current_key_index = batch_index % 5
                    print(
                        f"Processing batch {batch_index} with key index {current_key_index}"
                    )
                    future = executor.submit(
                        process_batch,
                        recipes_with_indices,
                        current_key_index,
                        flag_adder,
                    )
                    futures_dict[future] = batch_index
                    batch_index += 1

            # Process results as they complete while submitting new batches
            while futures_dict or current_line < total_lines:
                # If we have futures, process completed ones
                if futures_dict:
                    # Get the next completed future
                    for future in as_completed(futures_dict):
                        recipes_with_flags = future.result()
                        if recipes_with_flags:
                            _save_to_database(recipes_with_flags)
                            update_progress(current_line, count, total_lines)

                        # Remove the completed future
                        del futures_dict[future]

                        # If there are more lines to process, submit a new batch
                        if current_line < total_lines:
                            recipes_with_indices = []

                            # Read batch of 5 recipes
                            for j in range(5):
                                line = f.readline()
                                if not line.strip():
                                    break

                                recipe_data = json.loads(line)
                                recipes_with_indices.append((current_line, recipe_data))
                                count += 1
                                current_line += 1

                            if recipes_with_indices:
                                # Round-robin key assignment by index
                                current_key_index = batch_index % 5
                                print(
                                    f"Processing batch {batch_index} with key index {current_key_index}"
                                )
                                future = executor.submit(
                                    process_batch,
                                    recipes_with_indices,
                                    current_key_index,
                                    flag_adder,
                                )
                                futures_dict[future] = batch_index
                                batch_index += 1

                        # Exit the as_completed loop to check if we're done
                        break
                else:
                    # No more futures and no more lines to process
                    break

        f.close()
        print("Finished adding rows to database.")
        end_time = time.time()
        print(f"Time taken to process: {end_time - start_time} seconds")

    except KeyboardInterrupt:
        print(
            "\n\nKeyboard interrupt detected. Setting embeddings and saving progress..."
        )
        update_progress(current_line, count, total_lines)
        f.close()
        print("Progress saved. Exiting.")
