import os
import re
import ai_utils
import db_query_handler
import pprint
import time
import json

if __name__ == "__main__":
    database = db_query_handler.Database("recipes.db")
    model = ai_utils.AIUtils()
    mode = 2
    if mode == 0:
        initial_time = time.time()
        analysis = model._analyze_kitchen_image("general")

        print("Kitchen Analysis:")
        print(analysis)
        final_time = time.time()
        print(f"Time taken for analysis: {final_time - initial_time} seconds")
    elif mode == 1:
        print("Enter your SQL query prompt:")
        # prompt = input()

        # query = model.generate_sql_query(prompt, database.db_path)
        query = """
            SELECT *
            FROM recipes
            WHERE nationality = 'Asian' AND spice_level_score = 5
            ;
        """
        if query:
            print(f"Generated SQL Query: {query}")
            results = database.execute_query(query)
            if results is not None:
                print("Query Results:")
                pprint.pprint(results)
            else:
                print("Failed to execute the query.")

    elif mode == 2:
        print("Enter your prompt:")
        prompt = input()
        function_to_call, function_args = model.get_intended_function_and_argument(
            user_input=prompt,
            embedding=model.get_embeddings(prompt),
            image_path="/Users/berkan/Desktop/Projects/chef_bono/current_frame.jpg",
        )

        if not function_to_call or not function_args.get("user_request"):
            print("No function was called.")
            exit(0)

        print(f"Function to call: {function_to_call}")
        print(f"Arguments: {function_args['user_request']}")

        if function_to_call == "generate_sql":
            query = model.generate_sql_query(
                function_args["user_request"], database.db_path
            )
            results = ""
            if query:
                print(f"Generated SQL Query: {query}")
                results = database.execute_query(query)
                if results is not None:
                    print("Query Results:")
                    pprint.pprint(results)
                else:
                    print("Failed to execute the query.")
            else:
                print("Failed to generate a SQL query.")

            if results:

                keep_convo_alive = True
                user_input = (
                    "introduce these recipe(s) to the user like a chef and ask which one they want to follow through: "
                    + str(results)
                )
                chat = model._get_new_chat()
                while keep_convo_alive:

                    chefs_reponse, keep_convo_alive = model.talk_to_ai(
                        user_input=user_input,
                        chat=chat,
                    )

                    print(chefs_reponse)
                    user_input = input()
