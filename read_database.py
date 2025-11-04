import sqlite3
import json


def read_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    # Convert rows to list of dicts
    recipes = [dict(zip(columns, row)) for row in rows]
    return recipes


if __name__ == "__main__":
    recipes = read_recipes()
    for recipe in recipes:
        print(json.dumps(recipe, indent=2, ensure_ascii=False))
