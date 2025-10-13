"""Order class supporting Product and Addon line items."""
from __future__ import annotations
from typing import List, Tuple, Union
from .product import Product, Addon
import datetime

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

    def save_to_file(self, filename: str, tax: float = 0.0, tip: float = 0.0):
        """Append the order summary to a text file with timestamp, tax, and tip."""
        from datetime import datetime
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(f"Order Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            for item, qty in self.items:
                name = getattr(item, 'prodName', getattr(item, 'addonName', 'Item'))
                price = getattr(item, 'price', 0.0)
                f.write(f"{name} x{qty} @ ${price:.2f} = ${price*qty:.2f}\n")
            subtotal = self.total()
            total = subtotal + tax + tip
            f.write(f"Subtotal: ${subtotal:.2f}\n")
            f.write(f"Tax: ${tax:.2f}\n")
            f.write(f"Tip: ${tip:.2f}\n")
            f.write(f"Total: ${total:.2f}\n")
            f.write("-"*40 + "\n")
