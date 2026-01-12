import sqlite3


def clear_recipes():
    conn = sqlite3.connect("recipes.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes")
    conn.commit()
    conn.close()
    print("All recipes have been deleted.")


if __name__ == "__main__":
    clear_recipes()
