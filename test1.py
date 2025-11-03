import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types


class KitchenImageAnalyzer:
    """
    A class to analyze kitchen supplies and food images using Google Gemini AI.
    """

    def __init__(self, model_name="gemini-2.0-flash"):
        self.client, self.model = self._init_gemini(model_name)
        self.output_token_limit = self.model.output_token_limit

    def _init_gemini(self, name):
        load_dotenv()
        API_KEY = os.getenv("GOOGLE_API_KEY")

        client = genai.Client(api_key=API_KEY)
        model_name = name
        models_list = client.models.list(config={"page_size": 100})
        model = None

        print(f"Looking for model: {model_name}")
        for model1 in models_list:
            if model1.name == "models/" + model_name:
                model = model1
                print(f"Found model: {model1.name}")
                break

        if model is None:
            print(f"Model {model_name} not found.")
            raise ValueError(f"Model {model_name} not available")

        return client, model

    def _get_config(
        self, instruction, schema=None, temperature=0.7, top_p=0.9, top_k=40
    ):
        """Create configuration for image analysis"""
        generate_content_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=self.output_token_limit,
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_CIVIC_INTEGRITY",
                    threshold="BLOCK_NONE",
                ),
            ],
            response_mime_type="application/json",
            system_instruction=[
                types.Part.from_text(text=instruction),
            ],
            response_schema=schema,
        )
        return generate_content_config

    def _get_response(self, prompt, config):
        """Get response from the model"""
        try:

            print("Prompt:", prompt)
            print("Config:", config)
            print("Model:", self.model.name)
            response = self.client.models.generate_content(
                model=self.model.name,
                contents=prompt,
                config=config,
            )

            if response and hasattr(response, "parsed"):
                return response.parsed
            return None

        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def analyze_kitchen_image(self, image_path, analysis_type="general"):
        """
        say: hello world
        print: say hello world

        Analyze kitchen supplies and food images
        """
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return None

        instruction = f"""
        Analyze this kitchen image and identify:
        - Food items and their quantities/conditions
        - Kitchen supplies and utensils
        - Storage containers and their contents
        - Expiration dates if visible
        - Organization suggestions
        
        Analysis focus: {analysis_type}
        
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

        config = self._get_config(instruction=instruction, schema=schema)

        # Determine mime type based on file extension
        mime_type = "image/jpeg"
        if image_path.lower().endswith(".png"):
            mime_type = "image/png"
        elif image_path.lower().endswith(".webp"):
            mime_type = "image/webp"

        # Read and encode image
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
        except Exception as e:
            print(f"Error reading image file: {e}")
            return None

        prompt = [
            types.Part.from_text(text="Analyze this kitchen image:"),
            types.Part.from_bytes(data=image_data, mime_type=mime_type),
        ]

        return self._get_response(prompt, config)

    def analyze_multiple_images(self, image_paths, analysis_type="general"):
        """Analyze multiple kitchen images"""
        results = {}
        for i, image_path in enumerate(image_paths):
            print(f"Analyzing image {i+1}/{len(image_paths)}: {image_path}")
            result = self.analyze_kitchen_image(image_path, analysis_type)
            results[f"image_{i+1}"] = result
        return results


if __name__ == "__main__":
    try:
        analyzer = KitchenImageAnalyzer()
        print("Kitchen Image Analyzer initialized successfully!")

        while True:
            print("\n--- Kitchen Image Analysis ---")
            print("1. Analyze single image")
            print("2. Analyze multiple images")
            print("3. Exit")

            choice = input("Choose option (1-3): ").strip()

            if choice == "1":
                image_path = "current_frame.jpg"
                analysis_type = (
                    input(
                        "Analysis type (general/inventory/expiration/organization): "
                    ).strip()
                    or "general"
                )

                print("Analyzing image...")
                result = analyzer.analyze_kitchen_image(image_path, analysis_type)

                if result:
                    print(f"\n=== Kitchen Analysis Results ===")
                    print(json.dumps(result, indent=2))
                else:
                    print("Failed to analyze image.")

            elif choice == "2":
                image_paths = []
                print("Enter image paths (press Enter on empty line to finish):")
                while True:
                    path = input("Image path: ").strip()
                    if not path:
                        break
                    image_paths.append(path)

                if image_paths:
                    analysis_type = (
                        input(
                            "Analysis type (general/inventory/expiration/organization): "
                        ).strip()
                        or "general"
                    )
                    results = analyzer.analyze_multiple_images(
                        image_paths, analysis_type
                    )

                    print(f"\n=== Multiple Images Analysis Results ===")
                    print(json.dumps(results, indent=2))
                else:
                    print("No images provided.")

            elif choice == "3":
                print("Goodbye!")
                break

            else:
                print("Invalid option. Please choose 1, 2, or 3.")

    except ValueError as e:
        print(f"Error initializing analyzer: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
