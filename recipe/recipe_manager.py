from ai_logic import ai_utils


class Recipe:
    def __init__(
        self,
        id=None,
        name=None,
        ingredients=None,
        preparation=None,
        meal_type=None,
        main_ingredient=None,
        nationality=None,
        vegetarian=False,
        vegan=False,
        gluten_free=False,
        dairy_free=False,
        nut_free=False,
        high_fiber=False,
        weight_loss_diet=False,
        muscle_gain_bulking=False,
        balanced_healthy=False,
        carb_score=0.0,
        protein_score=0.0,
        fat_score=0.0,
        calorie_score=0.0,
        sugar_score=0.0,
        spice_level_score=0.0,
        preparation_time_score=0.0,
        preparation_difficulty_score=0.0,
        meal_class=None,
    ):
        self.id = id
        self.name = name
        self.ingredients = ingredients
        self.preparation = preparation
        self.meal_type = meal_type
        self.main_ingredient = main_ingredient
        self.nationality = nationality
        self.vegetarian = vegetarian
        self.vegan = vegan
        self.gluten_free = gluten_free
        self.dairy_free = dairy_free
        self.nut_free = nut_free
        self.high_fiber = high_fiber
        self.weight_loss_diet = weight_loss_diet
        self.muscle_gain_bulking = muscle_gain_bulking
        self.balanced_healthy = balanced_healthy
        self.carb_score = carb_score
        self.protein_score = protein_score
        self.fat_score = fat_score
        self.calorie_score = calorie_score
        self.sugar_score = sugar_score
        self.spice_level_score = spice_level_score
        self.preparation_time_score = preparation_time_score
        self.preparation_difficulty_score = preparation_difficulty_score
        self.meal_class = meal_class
        self.preparation_and_cooking_suggestion = (None,)
        self.serving_suggestion = (None,)
        self.safe_keeping_suggestion = (None,)

        self.steps = []


def build(query_result):
    recipe = Recipe()
    recipe.name = query_result["name"]
    recipe.ingredients = query_result["ingredients"]
    recipe.preparation = query_result["preparation"]
    recipe.meal_type = query_result["meal_type"]
    recipe.main_ingredient = query_result["main_ingredient"]
    recipe.nationality = query_result["nationality"]
    recipe.vegetarian = query_result["vegetarian"]
    recipe.vegan = query_result["vegan"]
    recipe.gluten_free = query_result["gluten_free"]
    recipe.dairy_free = query_result["dairy_free"]
    recipe.nut_free = query_result["nut_free"]
    recipe.high_fiber = query_result["high_fiber"]
    recipe.weight_loss_diet = query_result["weight_loss_diet"]
    recipe.muscle_gain_bulking = query_result["muscle_gain_bulking"]
    recipe.balanced_healthy = query_result["balanced_healthy"]
    recipe.carb_score = query_result["carb_score"]
    recipe.protein_score = query_result["protein_score"]
    recipe.fat_score = query_result["fat_score"]
    recipe.calorie_score = query_result["calorie_score"]
    recipe.sugar_score = query_result["sugar_score"]
    recipe.spice_level_score = query_result["spice_level_score"]
    recipe.preparation_time_score = query_result["preparation_time_score"]
    recipe.preparation_difficulty_score = query_result["preparation_difficulty_score"]
    recipe.meal_class = query_result["meal_class"]
    recipe.steps = get_steps(recipe)

    return recipe


def get_steps(recipe):
    model = ai_utils.AIUtils()

    return model.get_steps(recipe.name, recipe.ingredients, recipe.preparation)


def edit_recipe(recipe, prompt):
    model = ai_utils.AIUtils()

    return model.edit_recipe(recipe, prompt)
