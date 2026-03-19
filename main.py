import os
import re
import ai_utils
import db_query_handler
import pprint
import time
import json
import recipe_manager

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
        keep_convo_alive = True
        chat = model._get_new_chat()
        recipe = None
        while keep_convo_alive:
            prompt = input()
            function_to_call, function_args = model.get_intended_function_and_argument(
                user_input=prompt,
                embedding=model.get_embeddings(prompt),
                image_path="/Users/berkan/Desktop/Projects/chef_bono/current_frame.jpg",
                chat=chat,
            )

            if function_to_call == "generate_sql":
                query = model.generate_sql_query(
                    function_args["user_request"], database.db_path
                )
                results = ""
                if query:
                    # print(f"Generated SQL Query: {query}")
                    results = database.execute_query(query)
                    if results is not None:
                        # print("Query Results:")
                        pprint.pprint(results)
                    else:
                        print("Failed to execute the query.")
                else:
                    print("Failed to generate a SQL query.")

                if results:

                    user_input = (
                        "introduce these recipe(s) to the user like a chef and ask which one they want to follow through: "
                        + str(results)
                    )

                    chefs_reponse, keep_convo_alive = model.talk_to_ai(
                        user_input=user_input,
                        chat=chat,
                    )

                    print(chefs_reponse)

            elif function_to_call == "select_recipe":
                recipe_name = function_args["recipe_name"]
                results = database.get_recipe(recipe_name)
                # print(f"Selected Recipe: {recipe_name}")
                # print(results)
                recipe = recipe_manager.build(results)
                # print(f"recipe.steps: {recipe.steps}")

            elif function_to_call == "provide_cooking_instructions":

                recipe_info = f"""
                    Name: {recipe.name}
                    Ingredients: {recipe.ingredients}
                    Preparation: {recipe.preparation}
                    Meal Type: {recipe.meal_type}
                    Main Ingredient: {recipe.main_ingredient}
                    nationality={recipe.national},
                    vegetarian={recipe.vegetarian},
                    vegan={recipe.vegan},
                    gluten_free={recipe.gluten_free},
                    dairy_free={recipe.dairy_free},
                    nut_free={recipe.nut_free},
                    high_fiber={recipe.high_fiber},
                    weight_loss_diet={recipe.weight_loss_diet},
                    muscle_gain_bulking={recipe.muscle_gain_bulking},
                    balanced_healthy={recipe.balanced_healthy},
                    carb_score={recipe.carb_score},
                    protein_score={recipe.protein_score},
                    fat_score={recipe.fat_score},
                    calorie_score={recipe.calorie_score},
                    sugar_score={recipe.sugar_score},
                    spice_level_score={recipe.spice_level_score},
                    preparation_time_score={recipe.preparation_time_score},
                    preparation_difficulty_score={recipe.preparation_difficulty_score},
                    meal_class={recipe.meal_class},
                    
                """
                chefs_reponse, keep_convo_alive = model.follow_preparation(
                    user_input=user_input,
                    chat=chat,
                    generic_parameter=[recipe_info, recipe.steps],
                )

                print(chefs_reponse)

            elif function_to_call == "respond_to_user":
                chefs_reponse, keep_convo_alive = model.talk_to_ai(
                    user_input=user_input, chat=chat
                )

                print(chefs_reponse)
