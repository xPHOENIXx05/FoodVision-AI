import os
import requests

API_KEY = os.environ.get(
    "USDA_API_KEY",
    "ZRREJ2EWXdQvYYckq9EAQdlbKNSbn6Nbk8yybRbI",
)


def get_calories_from_api(food_name):
    try:
        url = (
            f"https://api.nal.usda.gov/fdc/v1/foods/search"
            f"?query={food_name}&api_key={API_KEY}"
        )

        response = requests.get(url)
        data = response.json()

        if "foods" not in data or len(data["foods"]) == 0:
            return None

        nutrients = data["foods"][0].get("foodNutrients", [])

        calories = protein = carbs = fat = "Unknown"

        for n in nutrients:
            name = n.get("nutrientName")
            value = n.get("value")

            if name == "Energy":
                calories = value
            elif name == "Protein":
                protein = value
            elif name == "Carbohydrate, by difference":
                carbs = value
            elif name == "Total lipid (fat)":
                fat = value

        return {
            "calories": calories,
            "serving": "100g",
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
        }

    except Exception as e:
        print("API ERROR:", e)
        return None