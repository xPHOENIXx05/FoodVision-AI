from source_loader import load_source

foods = load_source("data/knowledge_base/fruits.json")

print(type(foods))
print(len(foods))
