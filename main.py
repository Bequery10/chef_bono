import os
import re
from ai_logic import ai_utils
from database_utils import db_query_handler
import pprint
import time
import json
from recipe import recipe_manager
from tts_and_stt.tts import play
from tts_and_stt.stt import start_flask_app, listen
import warnings
import logging
from recording_utils.camera import get_frame

if __name__ == "__main__":

    logging.basicConfig(level=logging.ERROR)
    warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")

    database = db_query_handler.Database("database_utils/recipes.db")
    latest_query_result = None
    model = ai_utils.AIUtils()

    keep_convo_alive = True
    chat = model._get_new_chat()
    recipe = None

    flask_proc = start_flask_app()
    greeting = True

    prompt_list = [
        "Hi Chef Bono, can you suggest me some recipes with broccoli?",
        "First one sounds good.",
        "Yes but first, list the ingredients for me.",
        "Can you ommit the onions and garlic from the ingredients list?",
        "What are the preparation steps for this recipe?",
    ]
    i1 = 0
    try:
        while keep_convo_alive:
            print("Listening for user input...")
            # prompt = stt.listen(greeting=greeting)

            prompt = listen(greeting=greeting)
            print(f"User said: '{prompt}'")
            greeting = False
            image_path = "recording_utils/current_image.jpg"
            get_frame(path=image_path)
            function_to_call, function_args = None, None
            try:
                function_to_call, function_args = (
                    model.get_intended_function_and_argument(
                        user_input=prompt,
                        image_path=image_path,
                        chat=chat,
                    )
                )
            except Exception as e:
                logging.exception(
                    "Error determining function to call:"
                )  # Logs with full traceback

                continue

            if function_to_call == "filter_recipes_by_tags":
                query = model.filter_recipes_by_tags(
                    function_args["user_request"], database.db_path
                )
                if query:
                    # print(f"Generated SQL Query: {query}")
                    latest_query_result = database.execute_query(query)
                else:
                    print(
                        "Couldn't find any recipes matching your request. Please try again with different criteria."
                    )

                if latest_query_result:
                    user_input = function_args["user_request"]

                    query_result_string = ""
                    for result in latest_query_result:
                        query_result_string += f"name: {result['name']}\n"

                    chefs_response, keep_convo_alive = model.talk_to_ai(
                        user_input=user_input,
                        chat=chat,
                        generic_parameter=[query_result_string],
                    )

                    play(chefs_response)

            elif function_to_call == "vector_search_recipes":
                query = model.vector_search_recipes(
                    function_args["user_request"], database.db_path
                )
                if query:
                    # print(f"Generated Vector Search Query: {query}")
                    latest_query_result = database.execute_query(query)
                else:
                    print(
                        "Couldn't find recipes similar to your request. Please try again."
                    )

                if latest_query_result:
                    user_input = function_args["user_request"]

                    query_result_string = ""
                    for result in latest_query_result:
                        query_result_string += f"name: {result['name']}\n"

                    chefs_response, keep_convo_alive = model.talk_to_ai(
                        user_input=user_input,
                        chat=chat,
                        generic_parameter=[query_result_string],
                    )

                    play(chefs_response)

            elif function_to_call == "select_recipe":
                recipe_name = function_args["recipe_name"]

                print(f"Selecting recipe'{recipe_name}' from latest query results...")

                matches = [
                    recipe
                    for recipe in latest_query_result
                    if recipe["name"].replace(" ", "").lower()
                    == recipe_name.replace(" ", "").lower()
                ]
                result = matches[0] if matches else None

                # print(result)
                chefs_response = f"Great choice! You have selected the recipe: {result['name']}. I can list the ingredients, preparation steps, or edit the recipe for you. What would you like to do?"
                play(chefs_response)
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

                play(chefs_reponse)

            elif function_to_call == "edit_recipe":
                change = function_args["changes_to_be_made"]
                response = model.edit_recipe(
                    user_input=change,
                    recipe=recipe,
                )
                changes_made, main_ingredient, ingredients, preparation, steps = (
                    response[0]
                )
                keep_convo_alive = response[1]
                play(changes_made)
                chat._update_chat_history(prompt, changes_made)

            elif function_to_call == "respond_to_user":
                chefs_reponse = function_args["response"]
                chat._update_chat_history(prompt, chefs_reponse)
                play(chefs_reponse)
                print("program is continuing")

    except KeyboardInterrupt:
        flask_proc.terminate()
        os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")

    finally:
        flask_proc.terminate()
        os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
