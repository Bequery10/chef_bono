from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
import json
import threading
import os
import re
import sqlite3
import pprint
from building_phase import row_adder
import sqlite_vec
from sklearn.decomposition import PCA
import joblib
from database_utils import db_query_handler


class Chat:
    def __init__(
        self, input_token_limit, output_token_limit, context_window_limit, history=None
    ):
        self.input_token_limit = input_token_limit
        self.output_token_limit = output_token_limit
        self.context_window_limit = context_window_limit
        self.chat_history = history if history is not None else []
        self.started = False

    def _update_chat_history(self, prompt, output):

        if not self._is_list_of_parts(prompt):
            prompt = [types.Part.from_text(text=prompt)]
        if not self._is_list_of_parts(output):
            output = [types.Part.from_text(text=output)]

        self.chat_history.append(("user", prompt))
        self.chat_history.append(("assistant", output))

    def _pop_convo(self):
        if len(self.chat_history) < 2:
            print("No more conversation to pop.")
            return

        self.chat_history.pop()
        self.chat_history.pop()

    def _is_list_of_parts(self, obj):
        return isinstance(obj, list) and all(
            isinstance(item, types.Part) for item in obj
        )


class AIUtils:

    def __init__(self, model_name="gemini-2.5-flash-lite"):

        self.client, self.model = self._init_gemini(model_name, 0)
        self.input_token_limit = self.model.input_token_limit
        self.output_token_limit = self.model.output_token_limit
        self.context_window_limit = self.input_token_limit + self.output_token_limit
        self.start_time = 0
        self.waiting_time = 0
        self.started = False
        self.chat = Chat(
            self.input_token_limit,
            self.output_token_limit,
            self.context_window_limit,
        )

    def _init_gemini(self, name, key_index=0):
        load_dotenv()
        API_KEY = os.getenv("GOOGLE_API_KEY" + str(key_index))

        client = genai.Client(api_key=API_KEY)
        model_name = name
        models_list = client.models.list(config={"page_size": 5})
        model = None

        for model1 in models_list:
            if model1.name == "models/" + model_name:
                model = model1
                break

        return client, model

    def _start_timer(self):  # start the timer
        self.start_time = time.time()

    def _get_time(self):  # get the time since the timer started
        return time.time() - self.start_time

    def _estimate_image_token_cost(self, image_data, mime_type):
        # You need to know the image size (width, height)
        from PIL import Image
        import io

        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size
            if width <= 384 and height <= 384:
                return 258
            # For larger images, estimate tiles (each 768x768)
            tiles_w = (width + 767) // 768
            tiles_h = (height + 767) // 768
            return tiles_w * tiles_h * 258
        except Exception:
            # Fallback: assume 258 tokens
            return 258

    def _get_token_count(self, prompt):
        text = ""
        image_token_cost = 0
        for part in prompt:
            if hasattr(part, "text") and part.text:
                text += part.text + " "
            elif hasattr(part, "inline_data") and hasattr(part.inline_data, "data"):
                # Estimate image token cost
                image_token_cost += self._estimate_image_token_cost(
                    part.inline_data.data, part.inline_data.mime_type
                )
        # Count text tokens as before
        try:
            token_text = str(
                self.client.models.count_tokens(model=self.model.name, contents=text)
            ).split(" ")
            index = token_text[0].index("=") + 1
            token = int(token_text[0][index:])
            return token + image_token_cost
        except Exception as e:
            return image_token_cost

    def _check_for_exceptions(
        self, prompt
    ):  # checks for possible exceptions and fixes them BEFORE using the api

        if self._get_token_count(prompt) >= self.input_token_limit:
            print("Input window is full, please enter a shorter text.")
            return True

        return False

    def _fix_exceptions(self, e):  # fixes unforseen exceptions

        if not hasattr(e, "code"):
            print(f"An error occurred: {e}")
            return False  # failsafe

        if self.waiting_time == 0:
            current_time = int(self._get_time() % 60)
            self.waiting_time = current_time
        else:
            current_time = 60 - self.waiting_time
            self.waiting_time = 0

        if e.code == 429:

            error = json.loads(e.response.text)
            retry_delay = None
            for detail in error["error"].get("details", []):
                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                    retry_delay = detail.get("retryDelay")
                    break

            retry_delay = int(retry_delay[: retry_delay.rindex("s")])

            print(f"Resource exhausted, please wait {retry_delay} seconds to continue")
            time.sleep(retry_delay)
            return True  # retry the function

        if e.code == 503:
            print(f"An error occurred: {e}")
            print(
                f"Resource exhausted, please wait {60 - current_time} seconds to continue"
            )
            time.sleep(60 - current_time)
            return True  # retry the function

        else:
            print(f"An error occurred: {e}")
            return False  # failsafe

    def _get_config(
        self,
        instruction=None,
        schema=None,
        temperature=0.7,
        top_k=40,
        top_p=0.9,
    ):
        # Create configuration with system instruction
        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=self.output_token_limit,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",  # Block none
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",  # Block none
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE",  # Block none
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",  # Block none
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_CIVIC_INTEGRITY",
                    threshold="BLOCK_NONE",  # Block none
                ),
            ],
            response_mime_type="application/json",
            system_instruction=(
                [
                    types.Part.from_text(
                        text=instruction,
                    ),
                ]
            ),
            response_schema=schema,
        )

        return generate_content_config

    def _get_response(self, prompt, config, client):

        try:

            if self.start_time == 0:
                self._start_timer()

            response = client.models.generate_content(
                model=self.model.name,
                contents=prompt,
                config=config,
            )

        except Exception as e:
            print(f"An error occurred: {e}")
            if self._fix_exceptions(e):
                return self._get_response(prompt, config)

            return None

        if response is None:
            print("Response is None, please try again.")
            return ""

        return response

    def _check_context_window_limit(self, prompt, chat):

        total_tokens = self._get_token_count(prompt) + chat.output_token_limit

        if total_tokens > chat.context_window_limit:
            return True

        return False

    def _shrink_chat_history(self, chat, prompt, instruction):
        print("Shrinking chat history to fit in context window...")
        current_token = self._get_token_count(prompt + instruction)

        while current_token >= (chat.input_token_limit * 0.8):
            chat._pop_convo()
            current_token = self._get_token_count(
                chat._get_chat_history() + prompt + instruction
            )

    def _ask_and_check(
        self,
        prompt,
        chat,
        build_type=None,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        generic_parameter=None,
    ):

        score = 0
        attempt = 0
        response = None

        while score < 0.7 and attempt < 3:
            new_response = self._ask(
                prompt=prompt,
                chat=chat,
                build_type=build_type,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                generic_parameter=generic_parameter,
            )

            if new_response is None:
                print("No response from AI.")
                return None

            chat_history = []
            for role, parts in chat.chat_history:
                chat_history.extend(parts)

            new_score, feed_back = self._agent_check(
                previous_instruction=prompt,
                chat_history=chat_history,
                outputs=chat_history[-1] if chat_history else None,
            )

            if new_score > score:
                score = new_score
                response = new_response

            attempt += 1
            print(str(score) + "------------")
        return response

    def _ask(
        self,
        prompt,
        chat,
        build_type=None,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        generic_parameter=None,
        client=None,
        tools=None,
    ):
        if client is None:
            client = self.client

        print("Asking AI...")
        instruction, schema = self._get_build(
            build_type=build_type,
            generic_parameter=generic_parameter,
        )

        if self._check_for_exceptions(prompt):
            return ""

        response = ""

        config = None

        if not tools:
            config = self._get_config(
                instruction=instruction,
                schema=schema,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
            )

        else:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=[
                        tool["name"] for tool in self.get_tool_functions()
                    ],
                )
            )

            config = types.GenerateContentConfig(
                tools=[tools],
                top_p=top_p,
                top_k=top_k,
                temperature=temperature,
                tool_config=tool_config,
            )

        prompt_parts = []
        for role, parts in chat.chat_history:
            prompt_parts.extend(parts)

        prompt_parts.extend(prompt)

        exceed = self._check_context_window_limit(prompt_parts, chat)

        try:
            if not exceed:

                response = self._get_response(prompt_parts, config, client)
            else:
                self._shrink_chat_history(chat, prompt, instruction)

                response = self._get_response(prompt_parts, config, client)
        except Exception as e:
            print(e)
            print("Failed to get response from AI.")
            return None

        if (
            hasattr(response, "candidates")
            and len(response.candidates) > 0
            and hasattr(response.candidates[0].content.parts[0], "function_call")
            and response.candidates[0].content.parts[0].function_call is not None
        ):

            function_call = response.candidates[0].content.parts[0].function_call
            print(
                f"Function call detected: {function_call.name} with arguments {function_call.args}"
            )
            return function_call.name, function_call.args

        if response and hasattr(response, "parsed"):

            chat._update_chat_history(prompt, [self.to_gemini_text(response.parsed)])

            return response.parsed

        return None

    def _get_build(
        self,
        build_type,
        generic_parameter=None,
    ):

        instruction = None
        schema = None

        if build_type == "agent_check":
            feed_back = generic_parameter

            instruction = f"""
            You are an expert AI agent evaluator. Based on the system instruction, chat history, and outputs provided, you need to evaluate the performance of the AI agent.
            Please provide a score between 0 and 1, where 1 indicates excellent performance and 0 indicates poor performance. 
            Additionally, provide constructive feedback on how the AI agent can improve its performance.

            Use score and feed_back as the keys in your response JSON.
            """

            if feed_back:
                instruction += f"""
                Here is some additional feedback(s) to consider: {feed_back}
                """
            schema = {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "number",
                    },
                    "feed_back": {"type": "string"},
                },
                "required": ["score", "feed_back"],
            }

        elif build_type == "kitchen_image_analysis":
            analysis_focus = generic_parameter

            instruction = f"""
            Analyze this kitchen image and identify:
            - Food items and their quantities/conditions
            - Kitchen supplies and utensils
            - Storage containers and their contents
            - Expiration dates if visible
            - Organization suggestions
            
            Analysis focus: {analysis_focus}
            
            Provide detailed, practical information for kitchen management.
            """

            schema = {
                "type": "object",
                "properties": {
                    "food_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "quantity": {"type": "string"},
                                "condition": {"type": "string"},
                                "expiration_estimate": {"type": "string"},
                            },
                        },
                    },
                    "kitchen_supplies": {"type": "array", "items": {"type": "string"}},
                    "organization_tips": {"type": "string"},
                    "shopping_suggestions": {"type": "string"},
                },
                "required": ["food_items", "kitchen_supplies"],
            }

        elif build_type == "add_flags":

            meal_classes = [
                "Pasta",
                "Pizza",
                "Rice dish",
                "Noodle",
                "Burger",
                "Sandwich",
                "Wrap",
                "Taco",
                "Kebab",
                "Steak",
                "Grilled meat",
                "Fried chicken",
                "Seafood",
                "Curry",
                "Stew",
                "Casserole",
                "Salad",
                "Soup",
                "Bowl",
                "Fries",
                "Potato dish",
                "Bread",
                "Egg dish",
                "Pancake / waffle",
                "Dumplings",
                "Rolls",
                "Finger food",
                "Pastry",
                "Cake",
                "Cookie",
                "Ice cream",
                "Syrup dessert",
                "Coffee",
                "Tea",
                "Soft drink",
                "Smoothie / shake",
            ]
            instruction = f"""
            You are an expert AI that provide values for the categories based on the recipes provided.
            Analyze the recipes and for each provide an array of values of an integer category: meal_type, a string category: main_ingredient, nationality; boolean categories: 'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'nut-free', 'high_fiber', 'weight_loss/diet', 'muscle_gain/bulking', 'balanced/healthy' and float categories: 'carb_score', 'protein_score', 'fat_score', 'calorie_score', 'sugar_score', 'spice_level_score', 'preparation_time_score', 'preparation_difficulty_score' and for enum category 'meal_class'.
            Use the following guidelines to determine the values:
            For the integer category 'meal_type', provide 1 for breakfast, 2 for lunch, and 3 for dinner.
            For the string category 'main_ingredient', provide the primary ingredient used in the recipe. Make sure ingredient name is convential and straightforward like "chicken", "meat", "cucumber", "potato". For 'nationality', provide the cuisine type like "Italian", "Chinese", "Mexican", etc, if possible. If not possible, provide "Unknown". 
            For boolean categories, provide 'true' if the recipe fits the category, otherwise provide 'false'.
            For float categories, provide a score between 0 and 1 indicating how well the recipe provides the category.
            For the enum category 'meal_class', choose only one from the following list that best fits the recipe: {meal_classes}
            Provide the output in a JSON array format where each element corresponds to a recipe with the specified properties.
            Make sure the array's elements are in the same order as the input recipes.
            """

            schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "meal_type": {
                            "type": "number",
                            "minimum": 1,
                            "maximum": 3,
                        },
                        "main_ingredient": {"type": "string"},
                        "nationality": {"type": "string"},
                        "vegetarian": {"type": "boolean"},
                        "vegan": {"type": "boolean"},
                        "gluten_free": {"type": "boolean"},
                        "dairy_free": {"type": "boolean"},
                        "nut_free": {"type": "boolean"},
                        "high_fiber": {"type": "boolean"},
                        "weight_loss_diet": {"type": "boolean"},
                        "muscle_gain_bulking": {"type": "boolean"},
                        "balanced_healthy": {"type": "boolean"},
                        "carb_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "protein_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "fat_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "calorie_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "sugar_score": {"type": "number", "minimum": 0, "maximum": 1},
                        "spice_level_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "preparation_time_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "preparation_difficulty_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "meal_class": {
                            "type": "string",
                            "enum": meal_classes,
                        },
                    },
                    "required": [
                        "meal_type",
                        "main_ingredient",
                        "nationality",
                        "vegetarian",
                        "vegan",
                        "gluten_free",
                        "dairy_free",
                        "nut_free",
                        "high_fiber",
                        "weight_loss_diet",
                        "muscle_gain_bulking",
                        "balanced_healthy",
                        "carb_score",
                        "protein_score",
                        "fat_score",
                        "calorie_score",
                        "sugar_score",
                        "spice_level_score",
                        "preparation_time_score",
                        "preparation_difficulty_score",
                        "meal_class",
                    ],
                },
            }

        elif build_type == "query":
            db = sqlite3.connect("database_utils/recipes.db")

            db.enable_load_extension(True)
            sqlite_vec.load(db)
            db.enable_load_extension(False)
            cursor = db.cursor()
            table_sql = None
            with sqlite3.connect(generic_parameter[0]) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
                result = cursor.fetchone()
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE name='recipes_vec';"
                )
                result1 = cursor.fetchone()
                if result and result1:
                    table_sql = result[0] + "\n" + result1[0]

                embedding = generic_parameter[1]

                vec_sqlite_query_format_example = f"""
                        SELECT
                        recipes.*
                        FROM recipes_vec
                        JOIN recipes ON recipes_vec.rowid = recipes.id
                        WHERE recipes_vec.embedding MATCH [0.1, 0.2, 0.3, ..., 0.256]
                        ORDER BY recipes_vec.distance
                        LIMIT 3;
                        ;

                        //If you want to use vector search, you must use the MATCH clause with a query embedding
                        """
                instruction = f"""
                    You are an expert AI that fills sql query blocks to query the sqllite3 ({sqlite3.version_info}) database based on the user input.
                    Consider the given database structure when generating a query.
                    The sqllite3 database's "recipes" table's and "recipes_vec" structures: {table_sql}
                    If you need to perform nearest neighbor search,
                    here is the query format to perform nearest neighbor search using sqlite-vec extension:
                    {vec_sqlite_query_format_example}
                    Use the following keyword in your schema: SELECT, DISTINCT, COUNT, SUM, AVG, MIN, MAX, FROM, JOIN, ON, WHERE, MATCH, LIKE, GROUP BY, HAVING, ORDER BY, DESC, LIMIT.
                    If you don't neet any of the keywords of the keyword list, still include them in the response with empty string, None or false values.
                    If you must perform vector search, make sure to set FROM to "recipes_vec", JOIN to "recipes", ON to "recipes_vec.rowid = recipes.id", WHERE to "recipes_vec.embedding" and MATCH to True.

                    IMPORTANT:
                        There is only these 2 tables in the database: "recipes", "recipes_vec".
                        Make sure not to use any other table name in your query. 
                    """

            schema = {
                "type": "object",
                "properties": {
                    "SELECT": {
                        "type": "string",
                        "enum": [
                            "*",
                            "id",
                            "name",
                            "ingredients",
                            "preparation",
                            "meal_type",
                            "main_ingredient",
                            "nationality",
                            "vegetarian",
                            "vegan",
                            "gluten_free",
                            "dairy_free",
                            "nut_free",
                            "high_fiber",
                            "weight_loss_diet",
                            "muscle_gain_bulking",
                            "balanced_healthy",
                            "carb_score",
                            "protein_score",
                            "fat_score",
                            "calorie_score",
                            "sugar_score",
                            "spice_level_score",
                            "preparation_time_score",
                            "preparation_difficulty_score",
                            "meal_class",
                            "embedding",
                        ],
                        "example": "*",
                    },
                    "DISTINCT": {"type": "boolean", "example": False},
                    "COUNT": {"type": "boolean", "example": False},
                    "SUM": {
                        "type": "string",
                        "enum": [
                            "carb_score",
                            "protein_score",
                            "fat_score",
                            "calorie_score",
                            "sugar_score",
                            "spice_level_score",
                            "preparation_time_score",
                            "preparation_difficulty_score",
                        ],
                    },
                    "AVG": {
                        "type": "string",
                        "enum": [
                            "carb_score",
                            "protein_score",
                            "fat_score",
                            "calorie_score",
                            "sugar_score",
                            "spice_level_score",
                            "preparation_time_score",
                            "preparation_difficulty_score",
                        ],
                        "example": "carb_score",
                    },
                    "MIN": {
                        "type": "string",
                        "enum": [
                            "carb_score",
                            "protein_score",
                            "fat_score",
                            "calorie_score",
                            "sugar_score",
                            "spice_level_score",
                            "preparation_time_score",
                            "preparation_difficulty_score",
                        ],
                        "example": "carb_score",
                    },
                    "MAX": {
                        "type": "string",
                        "enum": [
                            "carb_score",
                            "protein_score",
                            "fat_score",
                            "calorie_score",
                            "sugar_score",
                            "spice_level_score",
                            "preparation_time_score",
                            "preparation_difficulty_score",
                        ],
                        "example": "carb_score",
                    },
                    "FROM": {
                        "type": "string",
                        "enum": ["recipes", "recipes_vec"],
                        "example": "recipes",
                    },
                    "JOIN": {
                        "type": "string",
                        "enum": ["recipes", "recipes_vec"],
                        "example": "recipes_vec",
                    },
                    "ON": {
                        "type": "string",
                        "example": "recipes.id = recipes_vec.rowid",
                    },
                    "WHERE": {
                        "type": "string",
                        "example": "spice_level_score > 0.5 AND vegetarian = true",
                    },
                    "MATCH": {
                        "type": "boolean",
                        "example": False,
                        "description": "True for vector search",
                    },
                    "LIKE": {"type": "string", "example": "%search_term%"},
                    "GROUP BY": {
                        "type": "string",
                        "enum": [
                            "meal_type",
                            "main_ingredient",
                            "nationality",
                            "vegetarian",
                            "vegan",
                            "gluten_free",
                            "dairy_free",
                            "nut_free",
                            "high_fiber",
                            "weight_loss_diet",
                            "muscle_gain_bulking",
                            "balanced_healthy",
                            "meal_class",
                        ],
                        "example": "meal_class",
                    },
                    "HAVING": {
                        "type": "string",
                        "example": "spice_level_score > 0.5 AND vegetarian = true",
                    },
                    "ORDER BY": {
                        "type": "string",
                        "enum": [
                            "id",
                            "name",
                            "meal_type",
                            "main_ingredient",
                            "nationality",
                            "carb_score",
                            "protein_score",
                            "fat_score",
                            "calorie_score",
                            "sugar_score",
                            "spice_level_score",
                            "preparation_time_score",
                            "preparation_difficulty_score",
                            "meal_class",
                        ],
                        "example": "spice_level_score",
                    },
                    "DESC": {"type": "boolean", "example": False},
                    "LIMIT": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "example": 10,
                    },
                },
                "required": ["SELECT", "FROM"],
            }
        elif build_type == "decide_intent":

            db = sqlite3.connect("database_utils/recipes.db")

            db.enable_load_extension(True)
            sqlite_vec.load(db)
            db.enable_load_extension(False)
            cursor = db.cursor()
            table_sql = None
            with sqlite3.connect("database_utils/recipes.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
                result = cursor.fetchone()
                cursor.execute(
                    "SELECT sql FROM sqlite_master WHERE name='recipes_vec';"
                )
                result1 = cursor.fetchone()
                if result and result1:
                    table_sql = result[0] + "\n" + result1[0]
                embedding = generic_parameter[0]

                vec_sqlite_query_format_example = f"""
                        SELECT
                        recipes.*
                        FROM recipes_vec
                        JOIN recipes ON recipes_vec.rowid = recipes.id
                        WHERE recipes_vec.embedding MATCH [0.1, 0.2, 0.3, ..., 0.256]
                        ORDER BY recipes_vec.distance
                        LIMIT 3;
                        ;

                        //If you want to use vector search, you must use the MATCH clause with a query embedding
                        """
                generate_sql_query_instruction = f"""
                    You can query the sqllite3 ({sqlite3.version_info}) database based on the user input.
                    The sqllite3 database's "recipes" table's and recipes_vec structures: {table_sql}
                    If you need to perform nearest neighbor search,
                    here is the query format to perform nearest neighbor search using sqlite-vec extension:
                    {vec_sqlite_query_format_example}
                    Consider the given database structure when generating a query.
                    Use the following keyword in your schema: SELECT, DISTINCT, COUNT, SUM, AVG, MIN, MAX, FROM, JOIN, ON, WHERE, MATCH, LIKE, GROUP BY, HAVING, ORDER BY, DESC, LIMIT.
                    If you don't neet any of the keywords of the keyword list, still include them in the response with empty string, None or false values.
                    If you must perform vector search, make sure to set FROM to "recipes_vec", JOIN to "recipes", ON to "recipes_vec.rowid = recipes.id", WHERE to "recipes_vec.embedding" and MATCH to True.
                """

                instruction = f"""
                    You are an AI assistant that choose a index and a parameter based on the intent of the user prompt.
                    Based on the function, you will provide an index and a parameter for the intent.

                    Use json schema to provide your response with the following keys:
                    - index: an integer that is between 0 and 3. Each index corresponds to a function that the AI agent will call based on the user intent.
                    - query_parameter: an object that contains the parameters for the function if the function requires a database query. The structure of the object should follow the SQL query format with keys like SELECT, FROM, WHERE, etc.
                    - generic_parameter: a string that contains the parameter for the function if the function requires a generic parameter. For example, it can be the name of the selected recipe or a human friendly response for the user input.


                    If the intent is about asking for a recipe(s), choose index 0 and use query_parameter in JSON SCHEMA to provide the parameter as an sql query in the following format: {generate_sql_query_instruction}
                    If the intent is about selecting a recipe based on the user input, chat history or image, choose index 1 and use generic_parameter in JSON SCHEMA to provide the name of the selected recipe.
                    If the intent is about asking for cooking instructions, ingredient information, nutritional information, or any other information about a recipe, choose index 2 you don't need to provide a parameter.
                    if the intent is about casual conversation, asking for cooking tips, asking for ingredient substitutes, or any other non-recipe-information-seeking intent, choose index 3 and use generic_parameter in JSON SCHEMA to provide a human friendly response to the user input.
                """

                schema = {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": "The index of the function to call based on the user intent.",
                        },
                        "query_parameter": {
                            "type": "object",
                            "properties": {
                                "SELECT": {"type": "string", "example": "*"},
                                "DISTINCT": {"type": "boolean", "example": False},
                                "COUNT": {"type": "boolean", "example": False},
                                "SUM": {"type": "string"},  # field to sum
                                "AVG": {
                                    "type": "string",
                                    "example": "field_name",
                                },  # field to average
                                "MIN": {
                                    "type": "string",
                                    "example": "field_name",
                                },  # field to get min
                                "MAX": {
                                    "type": "string",
                                    "example": "field_name",
                                },  # field to get max
                                "FROM": {"type": "string", "example": "recipes"},
                                "JOIN": {"type": "string", "example": "recipes_vec"},
                                "ON": {
                                    "type": "string",
                                    "example": " recipes.id = recipes_vec.rowid",
                                },
                                "WHERE": {
                                    "type": "string",
                                    "example": "spice_level_score > 0.5 AND vegetarian = true",
                                },  # list of filter objects
                                "MATCH": {
                                    "type": "boolean",
                                    "example": False,
                                    "description": "True for vector search",
                                },
                                "LIKE": {"type": "string", "example": "%search_term%"},
                                "GROUP BY": {"type": "string", "example": "field_name"},
                                "HAVING": {
                                    "type": "string",
                                    "example": "spice_level_score > 0.5 AND vegetarian = true",
                                },
                                "ORDER BY": {"type": "string", "example": "field_name"},
                                "DESC": {"type": "boolean", "example": False},
                                "LIMIT": {"type": "integer", "example": 10},
                            },
                            "required": [
                                "SELECT",
                                "DISTINCT",
                                "COUNT",
                                "SUM",
                                "AVG",
                                "MIN",
                                "MAX",
                                "FROM",
                                "JOIN",
                                "ON",
                                "WHERE",
                                "MATCH",
                                "LIKE",
                                "GROUP BY",
                                "HAVING",
                                "ORDER BY",
                                "DESC",
                                "LIMIT",
                            ],
                        },
                        "generic_parameter": {
                            "type": "string",
                        },
                    },
                }

        elif build_type == "talk":

            instruction = f"""
                You're a virtual chef, named Bono. Keep convos as informative and short as possible.
                Use json schema to provide your response with the following key:
                - chef's_response: a string that contains the response to the user input. The response should be human friendly and should be based on the user input, chat history, and kitchen image.
                - keep_convo_alive: a boolean that indicates whether the response should include a question or a statement that encourages the user to continue the conversation.
            """

            if generic_parameter and generic_parameter[0]:
                instruction += f"\nThese are the possible recipe options. They are queried from the database and provided to you to perform RAG as you form your answer:{generic_parameter[0]}"

            schema = {
                "type": "object",
                "properties": {
                    "chef's_response": {
                        "type": "string",
                    },
                    "keep_convo_alive": {
                        "type": "boolean",
                        "description": "Whether the response should include a question or a statement that encourages the user to continue the conversation.",
                    },
                },
                "required": ["chef's_response", "keep_convo_alive"],
            }

        elif build_type == "follow_preparation":
            instruction = f"""
                You are a virtual chef that helps the user follow the cooking steps and answer questions regarding them based on the selected recipe, user input, chat history, and kitchen image.
                Here is the recipe information:{generic_parameter[0]}
                Here are the steps for cooking: {generic_parameter[1]}
                Your responses should be clear, concise, and easy to follow, guiding the user through the cooking process effectively.
            """

            schema = {
                "type": "object",
                "properties": {
                    "cooking_instruction": {
                        "type": "string",
                    },
                    "keep_convo_alive": {
                        "type": "boolean",
                        "description": "Whether the response should include a question or a statement that encourages the user to continue the conversatio or go on with the next step.",
                    },
                },
                "required": ["cooking_instruction", "keep_convo_alive"],
            }

        elif build_type == "build_recipe":
            instruction = f"""
                You are an expert that will get recipe information and provide steps for cooking/preparation.
            """

            schema = {
                "type": "object",
                "properties": {
                    "cooking&preparation_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["cooking&preparation_steps"],
            }

        elif build_type == "edit_recipe":
            instruction = f"""
                You are an expert that will get recipe information and edit the recipe based on the user input.
                Following this schema:
                    - ingredients: a strings that contains the ingredients of the recipe.
                    - preparation: a strings that contains the preparation steps of the recipe.
                    - steps: an array of strings that contains the cooking steps of the recipe.
                    - main_ingredient: a string that contains the main ingredient of the recipe. It should be straightforward and conventional like "chicken", "beef", "cucumber", "potato", etc.
                    - keep_convo_alive: a boolean that indicates whether the response should include a question or a statement that encourages the user to continue the conversation.
            """

            schema = {
                "type": "object",
                "properties": {
                    "ingredients": {"type": "string"},
                    "preparation": {"type": "string"},
                    "steps": {"type": "array", "items": {"type": "string"}},
                    "main_ingredient": {"type": "string"},
                    "keep_convo_alive": {
                        "type": "boolean",
                        "description": "Whether the response should include a question or a statement that encourages the user to continue the conversation.",
                    },
                },
                "required": [
                    "ingredients",
                    "preparation",
                    "steps",
                    "main_ingredient",
                    "keep_convo_alive",
                ],
            }

        return instruction, schema

    def _start(self):
        self.started = True
        self._start_timer()

    def _agent_check(
        self,
        previous_instruction,
        chat_history,
        outputs,
    ):

        customized_prompt = []
        string1 = "The system instruction for the earliest:"
        string2 = "The chat history:"
        string3 = "The outputs that are produced based on the earliest response:"
        customized_prompt.append(self.to_gemini_text(text=string1))
        customized_prompt.extend(previous_instruction)
        customized_prompt.append(self._to_gemini_text(text=string2))
        customized_prompt.extend(chat_history)
        customized_prompt.append(self.to_gemini_text(text=string3))
        customized_prompt.extend(outputs)

        response = self._ask(
            prompt=customized_prompt,
            chat=self._get_new_chat(),
            build_type="agent_check",
            temperature=0.6,
            top_p=0.8,
            top_k=40,
        )

        if not response:
            print("No response from agent check.")
            return 0, ""

        return response["score"], response["feed_back"]

    def _get_new_chat(self):
        return Chat(
            self.input_token_limit,
            self.output_token_limit,
            self.context_window_limit,
        )

    def _add_flags(self, prompt):
        def insert_dict_at_index(d, index, key, value):
            items = list(d.items())
            items.insert(index, (key, value))
            return dict(items)

        gemini_prompt = [self.to_gemini_text(prompt)]

        response = self._ask(
            prompt=gemini_prompt,
            chat=self._get_new_chat(),
            build_type="add_flags",
        )
        # Update the dictionaries in the response list
        for i, recipe in enumerate(response):
            print(prompt[i]["name"])
            response[i] = insert_dict_at_index(recipe, 0, "embedding", [0.0] * 256)
        return response

    def _analyze_kitchen_image(self, analysis_focus, key_index=1):
        """Analyzes a kitchen image based on the provided focus."""

        prompt = []
        prompt.append(self.to_gemini_text("Analyze this kitchen image:"))
        prompt.append(self.to_gemini_image("current_frame.jpg"))

        client, model_nanme = self._init_gemini("gemini-2.5-flash-lite", key_index)

        response = self._ask(
            prompt=prompt,
            chat=self._get_new_chat(),
            build_type="kitchen_image_analysis",
            generic_parameter=analysis_focus,
            client=client,
        )

        print(json.dumps(response, indent=2))
        return response

    def get_intended_function_and_argument(
        self, user_input, embedding, image_path, chat=None
    ):
        if chat is None:
            chat = self._get_new_chat()
        client, model_nanme = self._init_gemini("gemini-2.5-flash-lite", 2)

        prompt = []
        prompt.append(self.to_gemini_text(user_input))
        prompt.append(self.to_gemini_text("Here is the image of the kitchen table:"))
        prompt.append(self.to_gemini_image(image_path))

        tools = types.Tool(function_declarations=self.get_tool_functions())
        current_time = time.time()

        response = self._ask(
            prompt=prompt,
            temperature=0.5,
            top_p=0.5,
            top_k=30,
            chat=chat,
            client=client,
            tools=tools,
        )

        print(
            f"Time taken for get_intended_function_and_argument: {time.time() - current_time:.2f} seconds"
        )

        return response

    def generate_sql_query(self, user_input, db_path):
        """Generates an SQL query based on user input and database structure."""
        embedding = self.get_embeddings([user_input])
        client, model_nanme = self._init_gemini("gemini-2.5-flash-lite", 2)

        prompt = []
        prompt.append(self.to_gemini_text(user_input))

        response = self._ask(
            prompt=prompt,
            top_k=1,
            top_p=0.1,
            temperature=0,
            chat=self._get_new_chat(),
            build_type="query",
            generic_parameter=[db_path, embedding],
            client=client,
        )

        if not response or "SELECT" not in response:
            print("Failed to generate SQL query.")
            return None

        return self.build_query(response, embedding)

    def to_gemini_text(self, obj):
        """
        Converts any Python object to a string suitable for types.Part.from_text.
        - dict/list: JSON string
        - str: as is
        - int/float/bool/None: str()
        """
        import json

        string = ""
        if isinstance(obj, (dict, list)):
            string = json.dumps(obj, ensure_ascii=False)
        elif isinstance(obj, str):
            string = obj
        elif obj is None:
            string = ""

        return types.Part.from_text(text=string)

    def to_gemini_image(self, image_path):
        """Converts an image file to types.Part with appropriate mime type."""
        import os

        mime_type = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime_type = "image/png"
        elif image_path.lower().endswith(".webp"):
            mime_type = "image/webp"

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
        except Exception as e:
            print(f"Error reading image file: {e}")
            return None

        return types.Part.from_bytes(data=image_data, mime_type=mime_type)

    def set_embeddings(self, key_index=0):

        db = sqlite3.connect("database_utils/recipes.db")
        import sqlite_vec

        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        cursor = db.cursor()
        recipes = cursor.execute("SELECT id, name, ingredients FROM recipes").fetchall()
        if not recipes:
            db.close()
            return

        model_name = "gemini-embedding-001"
        names_and_ingredients = [
            (name, ingredients) for _, name, ingredients in recipes
        ]
        embeddings = [
            self.client.models.embed_content(
                model=model_name,
                contents="recipe_name:" + name + "\n ingredients: " + ingredients,
            )
            .embeddings[0]
            .values
            for name, ingredients in names_and_ingredients
        ]
        n_samples = len(embeddings)
        n_features = len(embeddings[0])

        print("n_samples:", n_samples, "\nn_features:", n_features)
        n_components = min(256, n_samples)
        pca = PCA(n_components=n_components)
        embeddings_pca = pca.fit_transform(embeddings)

        joblib.dump(pca, "pca_model.joblib")

        for (recipe_id, _, _), embedding in zip(recipes, embeddings_pca):
            # Pad or truncate to 256 dimensions
            embedding = list(embedding)
            if len(embedding) < 256:
                embedding += [0.0] * (256 - len(embedding))
            elif len(embedding) > 256:
                embedding = embedding[:256]

            cursor.execute("DELETE FROM recipes_vec")
            cursor.execute(
                "REPLACE INTO recipes_vec(rowid, embedding) VALUES (?, ?)",
                (recipe_id, row_adder.serialize_f32(embedding)),
            )
        db.commit()
        db.close()

    def get_embeddings(self, texts, key_index=1):
        model_name = "gemini-embedding-001"
        embeddings = [
            self.client.models.embed_content(model=model_name, contents=text)
            .embeddings[0]
            .values
            for text in texts
        ]
        pca = joblib.load("ai_logic/pca_model.joblib")

        return pca.transform(embeddings)[0] if pca else embeddings

    def build_query(self, response, embedding):
        query = ""
        from_is_recipes = False
        for key in response:
            if response[key]:
                if not isinstance(response[key], bool):

                    if key == "FROM" and response[key] == "recipes":
                        from_is_recipes = True

                    elif key == "JOIN" and from_is_recipes:
                        continue

                    query += f" {key} {response[key]}"
                    query += "\n"
                else:
                    if response[key]:
                        query += f" {key}"

                        if key == "MATCH":
                            new_embedding = list(embedding)
                            if len(embedding) < 256:
                                new_embedding += [0.0] * (256 - len(embedding))

                            for key1 in response:
                                if key1 == "LIMIT":
                                    query += f" AND  recipes_vec.k = {response[key1]}"

                        query += "\n"

        query += ";"

        return query

    def get_tool_functions(self):

        generate_sql = {
            "name": "generate_sql",
            "description": (
                "Generates an SQL query to retrieve recipes based on a user's natural language request. "
                "Use this function to translate user prompts about recipes, ingredients, meal types, or dietary preferences into SQL queries. "
                "Examples: 'Find me vegetarian recipes with high spice level', 'Show me recipes suitable for dinner', "
                "'Show me recipes that have the ingredient on my kitchen table', 'Show me recipes like the ones on my kitchen table'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": (
                            "The user's request for generating an SQL query in natural language. "
                            "Examples: 'Find me vegetarian recipes with high spice level', "
                            "'Show me recipes suitable for dinner', "
                            "'Show me recipes that have the ingredient on my kitchen table', "
                            "'Show me recipes like the ones on my kitchen table'."
                        ),
                    },
                },
                "required": ["user_request"],
            },
        }

        select_recipe = {
            "name": "select_recipe",
            "description": (
                "Selects a recipe based on a user's natural language request. "
                "Use this function when the user specifies or refers to a particular recipe by name or by context from previous results. Make sure not to re-select the same recipe that is already selected in the previous conversation turns. "
                "Examples: 'I want an Old Italian Lasagna', 'Let's go with the first recipe in the query result', 'Beef Broccoli Wellington sounds nice.', 'yes', 'sure', 'let's go with that', 'sounds good'."
                "'Select the recipe suitable for dinner and with high spice level', 'Beef Broccoli Wellington sounds nice.'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {
                        "type": "number",
                        "description": (
                            "The exact id of the recipe to select, as specified or implied by the system prompt. "
                            "Examples: name: 'Beef Broccoli Wellington', id: '15' so choose '15', name: 'Spicy Thai Noodles', id: '26' so choose '26', name: 'Classic Beef Lasagna', id: '4' so choose '4' so choose '4'."
                        ),
                    },
                    "recipe_name": {
                        "type": "string",
                        "description": (
                            "The exact name of the recipe to select, as specified or implied by the system prompt. "
                            "Examples: 'Old Italian Lasagna', 'Beef Broccoli Wellington', 'Spicy Thai Noodles'."
                        ),
                    },
                },
                "required": ["recipe_id", "recipe_name"],
            },
        }

        follow_preparation = {
            "name": "follow_preparation",
            "description": (
                "Continues with the preparation of a selected recipe. "
                "This function should be called after getting a go for the response: 'Great choice! You have selected the recipe: 'recipe_name'. Let me provide you with the cooking/prepearing instructions and details for this recipe, If you wish.' from the user."
                "Use this function to guide the user through recipe steps, ingredients, or preparation details. "
                "Examples: 'Show me the next step', 'What ingredients do I need for the second step?', 'Can you explain how to prepare the sauce?', 'yes', 'let's start cooking', 'I'm ready', 'go ahead'."
                "'Can you explain how to prepare the sauce?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    # No parameters currently required, but can be extended for step-specific requests.
                },
                # No required parameters.
            },
        }

        respond_to_user = {
            "name": "respond_to_user",
            "description": (
                "Engages in a natural, conversational response to any user query or statement, regardless of topic. "
                "This includes casual questions, observations, or ambiguous requests related to cooking, kitchen items, or general conversation. "
                "Examples: 'What is on my kitchen table?', 'How does my dish look?', 'Do you think this dish would be delicious?', "
                "or any other open-ended or unclear user input."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "response": {
                        "type": "string",
                        "description": (
                            "A response in natural language to the user's input, which may be a casual question, observation, or ambiguous statement. "
                            "Examples: 'I am doing great, how are you ?', 'Your dish does look good!', "
                            "'I think this dish will be delicious', 'Do you want to ... (unidentifiable input)'."
                        ),
                    },
                },
                "required": ["response"],
            },
        }

        edit_recipe = {
            "name": "edit_recipe",
            "description": (
                "Edits the details of a selected recipe based on user input. "
                "Use this function when the user wants to modify the recipe's ingredients, preparation steps, or other details. "
                "Examples: 'I want to make this recipe vegan, what should I change?', 'Can you make this recipe gluten-free?', "
                "'I don't have broccoli, can you suggest a substitute and update the recipe accordingly?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    # Parameters for editing the recipe can be defined here based on expected user inputs for modifications.
                },
                # No required parameters currently, but can be extended as needed.
            },
        }
        # Return the list of function declarations
        return [
            generate_sql,
            select_recipe,
            follow_preparation,
            respond_to_user,
            edit_recipe,
        ]

    def talk_to_ai(self, user_input, chat, image_path=None, generic_parameter=None):
        prompt = []
        prompt.append(self.to_gemini_text(user_input))
        if image_path:
            prompt.append(self.to_gemini_text("Current view of the kitchen table:"))
            prompt.append(self.to_gemini_image(image_path))

        response = self._ask(
            prompt=prompt,
            chat=chat,
            build_type="talk",
            generic_parameter=generic_parameter,
        )

        if not response or "chef's_response" not in response:
            print("Failed to get a response from the AI.")
            return None

        return response["chef's_response"], response["keep_convo_alive"]

    def follow_preparation(
        self, user_input, chat, image_path=None, generic_parameter=None
    ):
        prompt = []
        prompt.append(self.to_gemini_text(user_input))
        if image_path:
            prompt.append(self.to_gemini_text("Image of the kitchen table:"))
            prompt.append(self.to_gemini_image(image_path))

        response = self._ask(
            prompt=prompt,
            chat=chat,
            build_type="follow_preparation",
            generic_parameter=generic_parameter,
        )

        if not response or "cooking_instruction" not in response:
            print("Failed to get a response from the AI.")
            return None

        return response["cooking_instruction"], response["keep_convo_alive"]

    def get_steps(self, recipe_name, ingredients, preparation):
        prompt = []
        prompt.append(self.to_gemini_text("Here is the recipe information:"))
        prompt.append(self.to_gemini_text(f"Recipe name: {recipe_name}"))
        prompt.append(self.to_gemini_text(f"Ingredients: {ingredients}"))
        prompt.append(self.to_gemini_text(f"Preparation: {preparation}"))
        prompt.append(
            self.to_gemini_text("Provide the steps for cooking/ preparing this recipe.")
        )

        response = self._ask(
            prompt=prompt,
            chat=self._get_new_chat(),
            build_type="build_recipe",
        )

        if not response or "cooking&preparation_steps" not in response:
            print("Failed to get a response from the AI.")
            return None

        return response["cooking&preparation_steps"]

    def edit_recipe(self, recipe, user_input):
        prompt = []
        prompt.append(
            self.to_gemini_text(
                "You need to edit the recipe based on the following prompt:"
            )
        )
        prompt.append(self.to_gemini_text(user_input))
        prompt.append(self.to_gemini_text("Here is the current recipe information:"))
        prompt.append(self.to_gemini_text(f"Recipe name: {recipe.name}"))
        prompt.append(self.to_gemini_text(f"Ingredients: {recipe.ingredients}"))
        prompt.append(self.to_gemini_text(f"Preparation: {recipe.preparation}"))
        prompt.append(self.to_gemini_text(f"Steps: {recipe.steps}"))

        response = self._ask(
            prompt=prompt,
            chat=self._get_new_chat(),
            build_type="edit_recipe",
        )

        if not response:
            print("Failed to get a response from the AI.")
            return None

        return (
            response["main_ingredient"],
            response["ingredients"],
            response["preparation"],
            response["steps"],
        ), response["keep_convo_alive"]
