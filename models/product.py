"""Product and Addon models aligned with group project database format.

The group project defines a multi-line record format inside text database files.
Fields (Products):
  prodID, prodName, prodDesc, prodPrice, prodStock, prodSales,
  prodBasedOn, prodPresetAddons, prodValidAddons, prodImg, prodImgSmall

Fields (Addons):
  prodID, prodName, prodDesc, prodPrice, prodStock, prodSales, prodImg, prodImgSmall
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Product:
    prodID: int
    prodName: str
    prodDesc: str
    prodPrice: float
    prodStock: int
    prodSales: int
    prodBasedOn: Optional[int]
    prodPresetAddons: str
    prodValidAddons: str
    prodImg: str
    prodImgSmall: str

    @property
    def price(self) -> float:  # legacy compatibility
        return self.prodPrice

    @property
    def stock(self) -> int:  # legacy compatibility
        return self.prodStock

    @property
    def id(self) -> int:  # convenience
        return self.prodID

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Product":
        return cls(
            prodID=int(d.get('prodID', 0)),
            prodName=d.get('prodName', ''),
            prodDesc=d.get('prodDesc', ''),
            prodPrice=float(d.get('prodPrice', 0.0)),
            prodStock=int(d.get('prodStock', 0)),
            prodSales=int(d.get('prodSales', 0)),
            prodBasedOn=_safe_int(d.get('prodBasedOn', '')),
            prodPresetAddons=d.get('prodPresetAddons', ''),
            prodValidAddons=d.get('prodValidAddons', ''),
            prodImg=d.get('prodImg', ''),
            prodImgSmall=d.get('prodImgSmall', ''),
        )


@dataclass
class Addon:
    addonID: int
    addonName: str
    addonDesc: str
    addonPrice: float
    addonStock: int
    addonSales: int
    addonImg: str
    addonImgSmall: str

    @property
    def price(self) -> float:  # compatibility
        return self.addonPrice

    @property
    def stock(self) -> int:
        return self.addonStock

    @property
    def id(self) -> int:
        return self.addonID

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Addon":
        return cls(
            addonID=int(d.get('prodID', 0)),
            addonName=d.get('prodName', ''),
            addonDesc=d.get('prodDesc', ''),
            addonPrice=float(d.get('prodPrice', 0.0)),
            addonStock=int(d.get('prodStock', 0)),
            addonSales=int(d.get('prodSales', 0)),
            addonImg=d.get('prodImg', ''),
            addonImgSmall=d.get('prodImgSmall', ''),
        )


def _safe_int(val: Any) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
