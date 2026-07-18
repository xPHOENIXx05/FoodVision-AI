from normalizer import normalize_name

samples = [
    " apple ",
    "BANANA",
    "  strawberry  ",
    "red delicious apple",
    "   grilled    cheese sandwich   ",
]

for sample in samples:
    print(f"{sample!r} -> {normalize_name(sample)!r}")