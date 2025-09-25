"""Order class supporting Product and Addon line items."""
from __future__ import annotations
from typing import List, Tuple, Union
from .product import Product, Addon

LineItem = Tuple[Union[Product, Addon], int]


class Order:
    def __init__(self):
        self.items: List[LineItem] = []

    def add_item(self, item: Union[Product, Addon], qty: int = 1):
        self.items.append((item, qty))

    def remove_last_item(self):
        if self.items:
            self.items.pop()

    def total(self) -> float:
        return sum(getattr(i, 'price', 0.0) * q for i, q in self.items)

    def summary(self) -> str:
        lines = ["Receipt Summary:"]
        for i, q in self.items:
            name = getattr(i, 'prodName', getattr(i, 'addonName', 'Item'))
            price = getattr(i, 'price', 0.0)
            lines.append(f"{name} x{q} @ ${price:.2f} = ${price * q:.2f}")
        lines.append("-" * 28)
        lines.append(f"Subtotal: ${self.total():.2f}")
        return "\n".join(lines)
