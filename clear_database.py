import sqlite3
import sqlite_vec


def clear_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    cursor.execute("DELETE FROM recipes")
    cursor.execute("DELETE FROM recipes_vec")
    conn.commit()
    conn.close()
    print("All recipes and recipe vectors have been deleted.")


if __name__ == "__main__":
    clear_recipes()
