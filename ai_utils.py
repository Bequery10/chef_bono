from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
import json
import threading
import os
import re
import sqlite3


class Chat:
    def __init__(
        self, input_token_limit, output_token_limit, context_window_limit, history=[]
    ):
        self.input_token_limit = input_token_limit
        self.output_token_limit = output_token_limit
        self.context_window_limit = context_window_limit
        self.chat_history = history
        self.started = False

    def _update_chat_history(self, prompt, output):
        self.chat_history.append(("user", prompt))
        self.chat_history.append(("assistant", output))

    def _pop_convo(self):
        if len(self.chat_history) < 2:
            print("No more conversation to pop.")
            return

        self.chat_history.pop()
        self.chat_history.pop()

    def _get_chat_history(self):
        convo_text = ""
        for role, text in self.chat_history:
            convo_text += f"{role}: {text}\n"
        return convo_text


class AIUtils:

    def __init__(self, model_name="gemini-2.0-flash"):

        self.client, self.model = self._init_gemini(model_name)
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

    def _init_gemini(self, name):
        load_dotenv()
        API_KEY = os.getenv("GOOGLE_API_KEY")

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

    def _get_token_count(self, text):  # get the token count of a given text
        try:
            token_text = str(
                self.client.models.count_tokens(model=self.model.name, contents=text)
            ).split(" ")
            index = token_text[0].index("=") + 1
            token = int(token_text[0][index:])
            return token
        except Exception as e:
            return 0

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
        self, instruction, schema=None, temperature=0.7, top_k=40, top_p=0.9
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
            system_instruction=[
                types.Part.from_text(
                    text=instruction,
                ),
            ],
            response_schema=schema,
        )

        return generate_content_config

    def _get_response(self, prompt, config):

        try:

            if self.start_time == 0:
                self._start_timer()

            response = self.client.models.generate_content(
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

    def _ask(
        self,
        prompt,
        chat,
        build_type=None,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        generic_parameter=None,
    ):
        instruction, schema = self._get_build(
            prompt=prompt,
            build_type=build_type,
            generic_parameter=generic_parameter,
        )

        if self._check_for_exceptions(prompt):
            return ""

        response = ""

        config = self._get_config(
            instruction=instruction,
            schema=schema,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
        )

        full_prompt = f"user: {prompt}\nchat_history: {chat._get_chat_history()}/"

        exceed = self._check_context_window_limit(full_prompt + instruction, chat)

        try:
            if not exceed:
                response = self._get_response(full_prompt, config)
            else:
                self._shrink_chat_history(chat, prompt, instruction)
                full_prompt = (
                    f"user: {prompt}\nchat_history: {chat._get_chat_history()}/"
                )
                response = self._get_response(full_prompt, config)

        except Exception as e:
            print(e)
            return None

        if response and hasattr(response, "parsed"):

            chat._update_chat_history(prompt, response.parsed)
            return response.parsed

    def _get_build(
        self,
        prompt,
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
            instruction = """
            You are an expert AI that provide values for the categories based on the recipes provided.
            Analyze the recipes and for each provide an array of values of the boolean categories: 'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'nut-free', 'high_fiber', 'weight_loss/diet', 'muscle_gain/bulking', 'balanced/healthy' and float categories: 'carb_score', 'protein_score', 'fat_score', 'calorie_score', 'sugar_score'.
            For boolean categories, provide 'true' if the recipe fits the category, otherwise provide 'false'.
            For float categories, provide a score between 0 and 1 indicating how well the recipe provides the category.
            Provide the output in a JSON array format where each element corresponds to a recipe with the specified properties.
            Make sure the array's elements are in the same order as the input recipes.
            """
            schema = {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "vegetarian": {"type": "boolean"},
                        "vegan": {"type": "boolean"},
                        "gluten_free": {"type": "boolean"},
                        "dairy_free": {"type": "boolean"},
                        "nut_free": {"type": "boolean"},
                        "high_fiber": {"type": "boolean"},
                        "weight_loss_diet": {"type": "boolean"},
                        "muscle_gain_bulking": {"type": "boolean"},
                        "balanced_healthy": {"type": "boolean"},
                        "carb_score": {"type": "number"},
                        "protein_score": {"type": "number"},
                        "fat_score": {"type": "number"},
                        "calorie_score": {"type": "number"},
                        "sugar_score": {"type": "number"},
                    },
                    "required": [
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
                    ],
                },
            }
        return instruction, schema

    def _start(self):
        self.started = True
        self._start_timer()

    def _agent_check(
        self,
        previous_instruction,
        chat,
        outputs,
    ):

        customized_prompt = f"""
        The system instruction for the earliest: {previous_instruction}
        The chat history: {chat.chat_history}
        The outputs that are produced based on the earliest response: {outputs}
        """
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
        response = self._ask(
            prompt=prompt,
            chat=self._get_new_chat(),
            build_type="add_flags",
        )

        return response

    def ask_ai(self):
        return None
