import sqlite3
import sqlite_vec
import os

import struct


def serialize_f32(vector):
    """Serializes a list of floats into a compact 'raw bytes' format."""
    return struct.pack("%sf" % len(vector), *vector)


# Create the database schema from SQL file
os.system("sqlite3 recipes.db < database_structure.sql")
conn = sqlite3.connect("recipes.db")
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

(sqlite_version, vec_version) = conn.execute(
    "select sqlite_version(), vec_version()"
).fetchone()
print(f"sqlite_version={sqlite_version}, vec_version={vec_version}")

conn.commit()
conn.close()
