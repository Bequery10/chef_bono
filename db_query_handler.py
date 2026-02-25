import sqlite3
import sqlite_vec


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
