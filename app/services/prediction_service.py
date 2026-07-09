def normalize_food_name(food_name):
    if not food_name:
        return None

    normalized = food_name.lower().strip()

    # Simple alias mapping for commonly misclassified names
    aliases = {
        'french fries': 'french fries',
        'fries': 'french fries',
        'hot dog': 'hot dog',
        'hamburger': 'burger',
        'ice cream': 'ice cream',
        'chicken wings': 'chicken wings',
        'pizza': 'pizza',
        'sushi': 'sushi',
        'tacos': 'tacos',
        'bibimbap': 'bibimbap',
        'burger': 'burger',
        'dosa': 'dosa',
        'salad': 'salad',
    }

    if normalized in aliases:
        return aliases[normalized]

    # remove punctuation and underscores
    normalized = normalized.replace('_', ' ').replace('-', ' ').strip()

    return normalized