import sqlite3
import sqlite_vec
from database_utils import read_database
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


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def execute_query(self, query, params=None):

        conn = sqlite3.connect("database_utils/recipes.db")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        cursor = conn.cursor()
        # Join recipes with recipes_vec to get the embedding
        cursor.execute(query, params or ())
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

    def get_recipe(self, recipe_name):
        query = f"SELECT * FROM recipes WHERE name = '{recipe_name}';"
        conn = sqlite3.connect(self.db_path)

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        recipe = {}
        for row in rows:
            for key, value in zip(columns, row):
                recipe[key] = read_database.serialize_bytes(value, key)
        cursor.close()
        conn.close()

        return recipe
