"""Inventory handler compatible with group project database format.

Parses the multi-line tagged records used in `default.txt` and `default_addons.txt`.
This stays minimal: it only loads data and provides simple lookup and stock update helpers.
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import os
from .product import Product, Addon

class Inventory:
    def __init__(self,
                 product_file: Optional[str] = None,
                 addon_file: Optional[str] = None):
        """Initialize inventory with optional explicit file paths.

        If paths are not provided, they are resolved relative to the project root (the
        folder containing this package) as:
          SDEV_220_Final_Project_Group2/DatabaseFiles/default.txt
          SDEV_220_Final_Project_Group2/DatabaseFiles/default_addons.txt
        This avoids depending on the current working directory when launching.
        """
        if product_file is None or addon_file is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))  # .../SDEV220
            db_dir = os.path.join(base_dir, "DatabaseFiles")
            product_file = product_file or os.path.join(db_dir, "default.txt")
            addon_file = addon_file or os.path.join(db_dir, "default_addons.txt")
        self.product_file = product_file
        self.addon_file = addon_file
        self.products: List[Product] = []
        self.addons: List[Addon] = []

    # --------------------- Parsing ---------------------
    def _parse_database_file(self, path: str, is_addon: bool) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not os.path.exists(path):
            return records
        current: Dict[str, Any] = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for raw in f:
                    if raw.startswith('//') or raw.strip() == '':
                        continue
                    line = raw.rstrip('\n')
                    if line.startswith('prodID=') and current:
                        # new record begins -> flush existing
                        records.append(current)
                        current = {}
                    if line.startswith('end_of_file'):
                        if current:
                            records.append(current)
                        break
                    if '=' in line:
                        k, v = line.split('=', 1)
                        current[k] = v
                else:
                    # file ended without explicit end_of_file
                    if current:
                        records.append(current)
        except Exception as e:
            print(f"Error reading {path}: {e}")
        return records

    def load(self):
        """Load both products and addons from configured files."""
        self.products.clear()
        self.addons.clear()
        for rec in self._parse_database_file(self.product_file, is_addon=False):
            try:
                self.products.append(Product.from_dict(rec))
            except Exception as e:
                print("Skip bad product record:", rec, e)
        for rec in self._parse_database_file(self.addon_file, is_addon=True):
            try:
                self.addons.append(Addon.from_dict(rec))
            except Exception as e:
                print("Skip bad addon record:", rec, e)

    # --------------------- Lookup Helpers ---------------------
    def get_product(self, pid: int) -> Optional[Product]:
        return next((p for p in self.products if p.prodID == pid), None)

    def get_addon(self, aid: int) -> Optional[Addon]:
        return next((a for a in self.addons if a.addonID == aid), None)

    def get_stock(self, pid: int, addon: bool = False) -> int:
        if addon:
            a = self.get_addon(pid)
            return a.stock if a else 0
        p = self.get_product(pid)
        return p.stock if p else 0

    def reduce_stock(self, pid: int, qty: int, addon: bool = False) -> bool:
        if addon:
            a = self.get_addon(pid)
            if a and a.addonStock >= qty:
                a.addonStock -= qty
                return True
            return False
        p = self.get_product(pid)
        if p and p.prodStock >= qty:
            p.prodStock -= qty
            return True
        return False

    # --------------------- Serialization (Optional) ---------------------
    def save_products(self):  # Minimal placeholder - format writing not fully specified
        # Not implemented: writing multi-line tagged format would mirror parsing order.
        pass