import os
import re
import ai_utils
import db_query_handler
import pprint
import time

if __name__ == "__main__":
    database = db_query_handler.Database("recipes.db")
    ai = ai_utils.AIUtils()
    mode = 0
    if mode == 0:
        initial_time = time.time()
        analysis = ai._analyze_kitchen_image("general")

        print("Kitchen Analysis:")
        print(analysis)
        final_time = time.time()
        print(f"Time taken for analysis: {final_time - initial_time} seconds")
    else:
        print("Enter your SQL query prompt:")
        prompt = input()

        query = ai.generate_sql_query(prompt, database.db_path)
        if query:
            print(f"Generated SQL Query: {query}")
            results = database.execute_query(query)
            if results is not None:
                print("Query Results:")
                pprint.pprint(results)
            else:
                print("Failed to execute the query.")
