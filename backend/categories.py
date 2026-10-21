FRUIT_WORDS = [
    "apple", "banana", "mango", "orange", "papaya", "pomegranate", "grapes",
    "watermelon", "water melon", "pineapple", "guava", "mousambi", "sapota",
    "chikoo", "jack fruit", "jackfruit", "coconut", "kinnow", "pears", "plum",
    "litchi", "lychee", "melon", "fig", "strawberry", "kiwi", "dates",
]

VEGETABLE_WORDS = [
    "tomato", "onion", "potato", "brinjal", "bhindi", "cabbage", "cauliflower",
    "carrot", "green chilli", "beans", "gourd", "cucumb", "pumpkin", "drumstick",
    "capsicum", "ginger(green)", "garlic", "coriander(leaves)", "methi", "spinach",
    "palak", "raddish", "radish", "beetroot", "tori", "ridgeguard", "snakeguard",
    "sweet potato", "tapioca", "colocasia", "peas wet", "lemon", "turnip",
    "amaranthus", "knool khol", "leafy vegetable", "mint", "curry leaves",
    "ladies finger", "pointed gourd", "elephant yam", "raw mango",
]


def get_category(commodity: str) -> str:
    name = (commodity or "").strip().lower()
    if "oil" in name:
        return "grocery"
    if "raw mango" in name:
        return "vegetable"
    for word in FRUIT_WORDS:
        if word in name:
            return "fruit"
    for word in VEGETABLE_WORDS:
        if word in name:
            return "vegetable"
    return "grocery"