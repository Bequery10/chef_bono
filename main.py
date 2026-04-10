import os
import re
from ai_logic import ai_utils
from database_utils import db_query_handler
import pprint
import time
import json
from recipe import recipe_manager
from tts_and_stt import tts
from tts_and_stt import stt

if __name__ == "__main__":
    database = db_query_handler.Database("database_utils/recipes.db")
    stt_model = stt.initialize_model()
    latest_query_result = None
    model = ai_utils.AIUtils()

    tts.play("Welcome, I am chef Bono !")
    keep_convo_alive = True
    chat = model._get_new_chat()
    recipe = None
    while keep_convo_alive:
        prompt = stt.listen(model=stt_model)
        function_to_call, function_args = None, None
        try:
            function_to_call, function_args = model.get_intended_function_and_argument(
                user_input=prompt,
                embedding=model.get_embeddings(prompt),
                image_path="/Users/berkan/Desktop/Projects/chef_bono/recording_utils/brocolli.png",
                chat=chat,
            )
        except Exception as e:
            print(f"Error determining function to call: {e}")
            continue

        if function_to_call == "generate_sql":
            query = model.generate_sql_query(
                function_args["user_request"], database.db_path
            )
            results = ""
            if query:
                # tts.play(f"Generated SQL Query: {query}")
                latest_query_result = database.execute_query(query)
                if not results:
                    print("Failed to execute the query.")
            else:
                print("Failed to generate a SQL query.")

            if latest_query_result:
                user_input = function_args["user_request"]
                chefs_reponse, keep_convo_alive = model.talk_to_ai(
                    user_input=user_input,
                    chat=chat,
                    generic_parameter=[
                        "name: " + result["name"] + ", id: " + str(result["id"])
                        for result in latest_query_result
                    ],
                )

                tts.play(chefs_reponse)

        elif function_to_call == "select_recipe":
            recipe_id = int(function_args["recipe_id"])
            recipe_name = function_args["recipe_name"]
            matches = [
                recipe for recipe in latest_query_result if recipe["id"] == recipe_id
            ]
            result = matches[0] if matches else None

            if not result:
                matches = [
                    recipe
                    for recipe in latest_query_result
                    if recipe["name"] == recipe_name
                ]
                result = matches[0] if matches else None

            print(result)
            chefs_response = f"Great choice! You have selected the recipe: {result['name']}. Let me provide you with the cooking/prepearing instructions and details for this recipe, If you wish."
            tts.play(chefs_response)
            recipe = recipe_manager.build(result)

            chat._update_chat_history(prompt, chefs_response)

        elif function_to_call == "follow_preparation":

            recipe_info = f"""
                Name: {recipe.name}
                Ingredients: {recipe.ingredients}
                Preparation: {recipe.preparation}
                Meal Type: {recipe.meal_type}
                Main Ingredient: {recipe.main_ingredient}
                nationality={recipe.nationality},
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
            user_input = prompt
            chefs_reponse, keep_convo_alive = model.follow_preparation(
                user_input=user_input,
                chat=chat,
                generic_parameter=[recipe_info, recipe.steps],
            )

            tts.play(chefs_reponse)

        elif function_to_call == "respond_to_user":
            chefs_reponse = function_args["response"]

            chat._update_chat_history(prompt, chefs_reponse)
            tts.play(chefs_reponse)
