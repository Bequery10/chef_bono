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
import requests

WEB_API_BASE = "http://127.0.0.1:5001"


def send_recipes_to_browser(recipes):
    """Send a list of recipes to the browser for display."""
    try:
        requests.post(
            f"{WEB_API_BASE}/control/recipes",
            json={"recipes": recipes},
            timeout=2,
        )
    except Exception as e:
        print(f"[WARNING] Failed to send recipes to browser: {e}")


def send_selected_recipe_to_browser(recipe):
    """Send a single selected recipe to the browser for detailed display."""
    try:
        requests.post(
            f"{WEB_API_BASE}/control/selected_recipe",
            json={"recipe": recipe},
            timeout=2,
        )
    except Exception as e:
        print(f"[WARNING] Failed to send selected recipe to browser: {e}")


if __name__ == "__main__":
    language = "english"
    logging.basicConfig(level=logging.ERROR)
    warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")

    database = db_query_handler.Database("database_utils/recipes.db")
    latest_query_result = None
    model = ai_utils.AIUtils(language=language)

    keep_convo_alive = True
    chat = model._get_new_chat()
    recipe = None

    flask_proc = start_flask_app(language=language)
    greeting = True

    prompt_list = [
        "Provide 5 avocado recipes.",
        "Provide 10 avocado recipes.",
        "select the first recipe in the list.",
        "Yes but first, list the ingredients for me.",
        "Can you ommit the onions and garlic from the ingredients list?",
        "What are the preparation steps for this recipe?",
    ]
    i1 = 0
    try:
        while keep_convo_alive:
            print("Listening for user input...")

            prompt = ""
            while not prompt:
                prompt = listen(greeting=greeting, language=language)

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
                        recipe_name=recipe.name if recipe else None,
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
                    send_recipes_to_browser(latest_query_result)

                user_input += "\n Your response will be read by a text-to-speech system, so please do not use any special characters, formatting or abbreviations in your response. Also, do not refer to recipes by their ids since those are not visible to the user. Refer to them by their names or by their context in the conversation. Your job is to provide a list of recipe names. Do not get into details of recipes."

                chefs_response, keep_convo_alive = model.talk_to_ai(
                    user_input=user_input,
                    chat=chat,
                    generic_parameter=[json.dumps(latest_query_result, indent=2)],
                )

                play(text=chefs_response, language=language)

            elif function_to_call == "vector_search_recipes":
                query = model.vector_search_recipes(
                    function_args["user_request"],
                    database.db_path,
                    limit_top_k=function_args["top_k"],
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
                    send_recipes_to_browser(latest_query_result)
                # print(f"Latest query result: {latest_query_result}")
                user_input += "\n Your response will be read by a text-to-speech system, so please do not use any special characters, formatting or abbreviations in your response. Also, do not refer to recipes by their ids since those are not visible to the user. Refer to them by their names or by their context in the conversation. Your job is to provide a list of recipe names. Do not get into details of recipes."

                chefs_response, keep_convo_alive = model.talk_to_ai(
                    user_input=user_input,
                    chat=chat,
                    generic_parameter=[json.dumps(latest_query_result, indent=2)],
                )

                play(text=chefs_response, language=language)

            elif function_to_call == "answer_questions_about_provided_recipes":
                user_input = function_args["user_question"]

                user_input += "\n Your response will be read by a text-to-speech system, so please do not use any special characters, formatting or abbreviations in your response. Also, do not refer to recipes by their ids since those are not visible to the user. Refer to them by their names or by their context in the conversation."
                chefs_response, keep_convo_alive = model.talk_to_ai(
                    user_input=user_input,
                    chat=chat,
                )

                play(text=chefs_response, language=language)

            elif function_to_call == "select_recipe":
                recipe_name = function_args["recipe_name"]
                recipe_index = function_args["recipe_index"]

                print(f"Selecting recipe'{recipe_name}' from latest query results...")

                result = (
                    latest_query_result[int(recipe_index) - 1] if recipe_index else None
                )

                # print(f"result: {result}")
                chefs_response = ""
                if language == "english":
                    chefs_response = f"Great choice! You have selected the recipe: {recipe_name}. I can list the ingredients, preparation steps, or edit the recipe for you. What would you like to do?"
                elif language == "turkish":
                    chefs_response = f"Seçiminiz {recipe_name}. Malzemelerini, hazırlık adımlarını listeleyebilir veya tarifi sizin için düzenleyebilirim. Ne yapmak istersiniz?"

                play(text=chefs_response, language=language)
                recipe = recipe_manager.build(result)

                new_result = result.copy()
                new_result["steps"] = recipe.steps
                send_recipes_to_browser([new_result])

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
                user_input += "\n Your response will be read by a text-to-speech system, so please do not use any special characters, formatting or abbreviations in your response."
                chefs_reponse, keep_convo_alive = model.follow_preparation(
                    user_input=user_input,
                    chat=chat,
                    generic_parameter=[recipe_info, recipe.steps],
                )

                play(text=chefs_reponse, language=language)

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
                play(text=changes_made, language=language)
                chat._update_chat_history(prompt, changes_made)

            elif function_to_call == "respond_to_user":
                chefs_reponse = function_args["response"]
                chat._update_chat_history(prompt, chefs_reponse)
                play(text=chefs_reponse, language=language)
                print("program is continuing")

    except KeyboardInterrupt:
        flask_proc.terminate()
        os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")

    finally:
        flask_proc.terminate()
        os.system("lsof -ti:5001 | xargs kill -9 2>/dev/null || true")
