import os
import re
import ai_utils
import db_query_handler
import pprint

if __name__ == "__main__":
    database = db_query_handler.Database("recipes.db")
    ai = ai_utils.AIUtils()
    mode = 1
    if mode == 0:
        analysis = ai._analyze_kitchen_image("general")

        print("Kitchen Analysis:")
        print(analysis)
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
