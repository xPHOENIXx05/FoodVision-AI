"""Static Food-101 class mapping for FoodVision knowledge-base collections."""

EXPECTED_FOOD101_CLASS_COUNT = 101

FOODVISION_COLLECTIONS = {
    "fruits",
    "vegetables",
    "proteins",
    "seafood",
    "dairy",
    "grains",
    "desserts",
    "snacks",
    "drinks",
    "fast_food",
    "restaurant_foods",
    "street_foods",
    "regional_foods",
}

FOOD101_COLLECTION_MAP: dict[str, str] = {
    "apple_pie": "desserts",
    "baby_back_ribs": "proteins",
    "baklava": "desserts",
    "beef_carpaccio": "proteins",
    "beef_tartare": "proteins",
    "beet_salad": "vegetables",
    "beignets": "desserts",
    "bibimbap": "regional_foods",
    "bread_pudding": "desserts",
    "breakfast_burrito": "fast_food",
    "bruschetta": "snacks",
    "caesar_salad": "vegetables",
    "cannoli": "desserts",
    "caprese_salad": "vegetables",
    "carrot_cake": "desserts",
    "ceviche": "seafood",
    "cheesecake": "desserts",
    "cheese_plate": "dairy",
    "chicken_curry": "regional_foods",
    "chicken_quesadilla": "fast_food",
    "chicken_wings": "fast_food",
    "chocolate_cake": "desserts",
    "chocolate_mousse": "desserts",
    "churros": "desserts",
    "clam_chowder": "seafood",
    "club_sandwich": "fast_food",
    "crab_cakes": "seafood",
    "creme_brulee": "desserts",
    "croque_madame": "regional_foods",
    "cup_cakes": "desserts",
    "deviled_eggs": "proteins",
    "donuts": "desserts",
    "dumplings": "regional_foods",
    "edamame": "vegetables",
    "eggs_benedict": "proteins",
    "escargots": "proteins",
    "falafel": "regional_foods",
    "filet_mignon": "proteins",
    "fish_and_chips": "seafood",
    "foie_gras": "proteins",
    "french_fries": "fast_food",
    "french_onion_soup": "regional_foods",
    "french_toast": "grains",
    "fried_calamari": "seafood",
    "fried_rice": "regional_foods",
    "frozen_yogurt": "desserts",
    "garlic_bread": "grains",
    "gnocchi": "regional_foods",
    "greek_salad": "vegetables",
    "grilled_cheese_sandwich": "fast_food",
    "grilled_salmon": "seafood",
    "guacamole": "snacks",
    "gyoza": "regional_foods",
    "hamburger": "fast_food",
    "hot_and_sour_soup": "regional_foods",
    "hot_dog": "fast_food",
    "huevos_rancheros": "regional_foods",
    "hummus": "snacks",
    "ice_cream": "desserts",
    "lasagna": "regional_foods",
    "lobster_bisque": "seafood",
    "lobster_roll_sandwich": "seafood",
    "macaroni_and_cheese": "regional_foods",
    "macarons": "desserts",
    "miso_soup": "regional_foods",
    "mussels": "seafood",
    "nachos": "fast_food",
    "omelette": "proteins",
    "onion_rings": "fast_food",
    "oysters": "seafood",
    "pad_thai": "regional_foods",
    "paella": "regional_foods",
    "pancakes": "grains",
    "panna_cotta": "desserts",
    "peking_duck": "regional_foods",
    "pho": "regional_foods",
    "pizza": "fast_food",
    "pork_chop": "proteins",
    "poutine": "fast_food",
    "prime_rib": "proteins",
    "pulled_pork_sandwich": "fast_food",
    "ramen": "regional_foods",
    "ravioli": "regional_foods",
    "red_velvet_cake": "desserts",
    "risotto": "regional_foods",
    "samosa": "street_foods",
    "sashimi": "seafood",
    "scallops": "seafood",
    "seaweed_salad": "vegetables",
    "shrimp_and_grits": "seafood",
    "spaghetti_bolognese": "regional_foods",
    "spaghetti_carbonara": "regional_foods",
    "spring_rolls": "street_foods",
    "steak": "proteins",
    "strawberry_shortcake": "desserts",
    "sushi": "regional_foods",
    "tacos": "street_foods",
    "takoyaki": "street_foods",
    "tiramisu": "desserts",
    "tuna_tartare": "seafood",
    "waffles": "grains",
}


def get_collection(class_name: str) -> str:
    """Return the FoodVision collection for a Food-101 class name."""

    try:
        return FOOD101_COLLECTION_MAP[class_name]
    except KeyError:
        raise KeyError(
            f"No Food-101 collection mapping found for '{class_name}'"
        ) from None


def validate_mapping_coverage(class_names: list[str]) -> None:
    """Validate that all supplied Food-101 classes have static mappings."""

    if len(FOOD101_COLLECTION_MAP) != EXPECTED_FOOD101_CLASS_COUNT:
        raise ValueError(
            "Food-101 mapping must contain "
            f"{EXPECTED_FOOD101_CLASS_COUNT} classes; found "
            f"{len(FOOD101_COLLECTION_MAP)}"
        )

    invalid_collections = sorted(
        {
            collection
            for collection in FOOD101_COLLECTION_MAP.values()
            if collection not in FOODVISION_COLLECTIONS
        }
    )

    if invalid_collections:
        raise ValueError(
            "Invalid FoodVision collection mappings: "
            + ", ".join(invalid_collections)
        )

    missing = sorted(set(class_names) - set(FOOD101_COLLECTION_MAP))

    if missing:
        raise ValueError(
            "Missing Food-101 collection mappings: "
            + ", ".join(missing)
        )

    extra = sorted(set(FOOD101_COLLECTION_MAP) - set(class_names))

    if extra:
        raise ValueError(
            "Unknown Food-101 mappings: " + ", ".join(extra)
        )