from dataclasses import dataclass

@dataclass
class MenuItem:
    id: str
    name: str
    price: float

BURGER_MENU = [
    MenuItem("b1", "Cheeseburger", 12.99),
    MenuItem("b2", "Double Bacon", 16.99),
    # ...
]
