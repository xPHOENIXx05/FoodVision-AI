from app.services.food101_service import predict_food

IMAGE_PATH = "test.jpg"   # Replace with the name of your test image

with open(IMAGE_PATH, "rb") as image_file:
    food_name, confidence, predictions = predict_food(image_file)

print(f"Prediction : {food_name}")
print(f"Confidence : {confidence:.2%}")

print("\nTop 3 Predictions:")
for p in predictions:
    print(f"- {p['name']} ({p['confidence']:.2f}%)")