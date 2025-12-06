import os
import re
import ai_utils
import db_query_handler

if __name__ == "__main__":
    database = db_query_handler.Database("recipes.db")
    ai = ai_utils.AIUtils()

    analysis = ai._analyze_kitchen_image("general")

    print("Kitchen Analysis:")
    for item, status in analysis.items():
        print(f"{item}: {status}")
    # prompt = input()

    # query = ai.generate_sql_query(prompt, database.db_path)
    # if query:
    #     print(f"Generated SQL Query: {query}")
    #     results = database.execute_query(query)
    #     if results is not None:
    #         print("Query Results:")
    #         for row in results:
    #             print(row)
    #     else:
    #         print("Failed to execute the query.")
