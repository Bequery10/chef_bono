import sqlite3
import json
import base64
import struct


def deserialize_embedding(b):
    if b is None:
        return None
    if isinstance(b, str):
        b = base64.b64decode(b)
    if len(b) % 4 != 0:
        return b
    n = len(b) // 4
    return list(struct.unpack(f"{n}f", b))


def serialize_bytes(obj, key=None):
    if key == "embedding" and obj is not None:
        return deserialize_embedding(obj)
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    return obj


def read_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    recipes = []
    for row in rows:
        recipe = {}
        for key, value in zip(columns, row):
            recipe[key] = serialize_bytes(value, key)
        recipes.append(recipe)
    return recipes


if __name__ == "__main__":
    recipes = read_recipes()
    for recipe in recipes:
        print(json.dumps(recipe, indent=2, ensure_ascii=False))
