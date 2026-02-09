import requests
from bs4 import BeautifulSoup
import time
import random
import os
import pickle
import json


def get_with_retries(url, retries=5, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response
            else:
                print(f"Non-200 status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt+1}): {e}")
        time.sleep(delay)
    return None


def _scrap_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    name_tag = soup.find("p", class_="H2")
    recipe_name = name_tag.get_text(strip=True) if name_tag else None

    # Extract ingredients
    ingredients_table = soup.find("span", string="ingredients")
    ingredients = None
    if ingredients_table:
        ingredients_p = ingredients_table.find_next("p", class_="H1")
        ingredients = (
            ingredients_p.get_text(separator="\n", strip=True)
            if ingredients_p
            else None
        )

    # Extract preparation
    prep_table = soup.find("span", string="preparation")
    preparation = None
    if prep_table:
        prep_p = prep_table.find_next("p", class_="H1")
        preparation = prep_p.get_text(separator="\n", strip=True) if prep_p else None

    return {"name": recipe_name, "ingredients": ingredients, "preparation": preparation}


def _save_bool_arr_at_index(index, value, filename="bool_array.bin"):
    with open(filename, "r+b") as f:
        f.seek(index)
        f.write(bytes([value]))


def _init_bool_arr(size, filename="bool_array.bin"):
    if not os.path.exists(filename):
        with open(filename, "wb") as f:
            f.write(bytes([0]) * size)


def _read_bool_arr(index, filename="bool_array.bin"):
    with open(filename, "rb") as f:
        f.seek(index)
        return bool(f.read(1)[0])


if __name__ == "__main__":

    if not os.path.exists("bool_array.bin"):
        _init_bool_arr(1086441)

    saved_recipe_count = sum(
        1 for _ in open("scraped_recipes.jsonl", "r", encoding="utf-8")
    )
    limit = 1086441 - saved_recipe_count
    start_time = time.time()
    with open("scraped_recipes.jsonl", "a", encoding="utf-8") as f:
        for i in range(limit):

            index = random.randint(1, 1086441)
            if _read_bool_arr(index - 1):
                continue
            response = get_with_retries(
                f"https://cookbooks.com/Recipe-Details.aspx?id={index}"
            )
            if response is None:
                print("Failed to retrieve the webpage.")
                exit()

            recipe = _scrap_html(response.text)

            if not (recipe["name"] and recipe["ingredients"] and recipe["preparation"]):
                _save_bool_arr_at_index(index - 1, 1)
                continue

            f.write(json.dumps(recipe, ensure_ascii=False) + "\n")
            _save_bool_arr_at_index(index - 1, 1)
            if i % 10 == 0:
                print(f"Scraped {i} recipes so far...")
        print(f"Scraping completed in {time.time() - start_time:.2f} seconds.")
