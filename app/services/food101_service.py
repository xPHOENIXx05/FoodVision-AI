from io import BytesIO

from PIL import Image
from transformers import pipeline

# Load the pretrained image classification pipeline once when the app starts.
classifier = pipeline(
    "image-classification",
    model="nateraw/food"
)


def predict_food(image_file):
    """
    Predict food from an uploaded image.

    Returns:
        food_name (str)
        confidence (float)
        predictions_list (list)
    """

    # Support both raw bytes (Flask) and file objects (tests)
    if isinstance(image_file, bytes):
        image = Image.open(BytesIO(image_file)).convert("RGB")
    else:
        image = Image.open(image_file).convert("RGB")

    results = classifier(image)

    top3 = results[:3]

    food_name = top3[0]["label"]
    confidence = top3[0]["score"]

    predictions_list = [
        {
            "name": item["label"],
            "confidence": round(item["score"] * 100, 2)
        }
        for item in top3
    ]

    return food_name, confidence, predictions_list