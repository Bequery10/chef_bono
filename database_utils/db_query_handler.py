import sqlite3
import sqlite_vec
from database_utils import read_database


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def execute_query(self, query, params=None):
        conn = sqlite3.connect(self.db_path)

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            conn.commit()
            return results
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

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
