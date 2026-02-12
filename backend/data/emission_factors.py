"""
EcoFlow LCA — Emission Factors Database
Single source of truth for all material and process impact factors.
Units: kg CO2e per kg of material (cradle-to-gate) unless noted.
Sources: ecoinvent 3.9, EPA WARM, Carbon Footprint Ltd, peer-reviewed LCA literature.
"""

# ---------------------------------------------------------------------------
# Material emission factors (kg CO2e / kg, cradle-to-gate)
# ---------------------------------------------------------------------------
MATERIAL_FACTORS: dict[str, float] = {
    # Plastics
    "hdpe": 2.6,
    "ldpe": 2.9,
    "pp": 1.95,
    "pet": 3.12,
    "pvc": 3.1,
    "abs": 3.55,
    "polycarbonate": 5.5,
    "polystyrene": 3.4,
    "nylon": 9.0,
    "acrylic": 5.2,
    "polyurethane": 4.2,
    "silicone": 6.0,
    "epoxy": 5.8,
    "eva": 2.8,
    "tpu": 4.0,
    # Metals
    "steel": 2.0,
    "recycled_steel": 0.7,
    "aluminum": 14.8,
    "recycled_aluminum": 1.7,
    "copper": 4.0,
    "zinc": 3.1,
    "tin": 16.0,
    "brass": 3.5,
    "stainless_steel": 6.15,
    "titanium": 35.0,
    "nickel": 12.0,
    # Natural / Organic
    "cotton": 6.5,
    "wool": 17.0,
    "leather": 17.0,
    "silk": 30.0,
    "softwood": -1.5,
    "hardwood": -1.2,
    "bamboo": -1.0,
    "natural_rubber": 3.0,
    "cork": -1.5,
    "jute": 0.5,
    # Minerals / Ceramics
    "glass": 1.25,
    "concrete": 0.13,
    "ceramic": 0.7,
    "clay": 0.3,
    "stone": 0.7,
    # Paper / Packaging
    "cardboard": 1.3,
    "paper": 1.1,
    "recycled_paper": 0.7,
    # Other / Composites
    "carbon_fiber": 30.0,
    "fiberglass": 8.0,
    "polyester_fabric": 5.5,
    "acetal": 3.8,
    "ptfe": 10.0,
    "lithium_ion_battery": 12.5,
}

DEFAULT_MATERIAL_FACTOR = 3.0  # median fallback for unknown materials

# ---------------------------------------------------------------------------
# Material aliases — maps common LLM output names to canonical keys
# ---------------------------------------------------------------------------
MATERIAL_ALIASES: dict[str, str] = {
    "plastic": "abs",
    "plastics": "abs",
    "metal": "steel",
    "iron": "steel",
    "stainless": "stainless_steel",
    "aluminium": "aluminum",
    "alu": "aluminum",
    "wood": "softwood",
    "timber": "softwood",
    "lumber": "softwood",
    "oak": "hardwood",
    "walnut": "hardwood",
    "maple": "hardwood",
    "teak": "hardwood",
    "pine": "softwood",
    "cedar": "softwood",
    "rubber": "natural_rubber",
    "synthetic_rubber": "tpu",
    "foam": "polyurethane",
    "pu_foam": "polyurethane",
    "memory_foam": "polyurethane",
    "polyethylene": "hdpe",
    "pe": "hdpe",
    "polypropylene": "pp",
    "polyester": "polyester_fabric",
    "neoprene": "natural_rubber",
    "spandex": "nylon",
    "elastane": "nylon",
    "lycra": "nylon",
    "teflon": "ptfe",
    "delrin": "acetal",
    "pom": "acetal",
    "pc": "polycarbonate",
    "ps": "polystyrene",
    "eps": "polystyrene",
    "styrofoam": "polystyrene",
    "kraft": "cardboard",
    "paperboard": "cardboard",
    "corrugated": "cardboard",
    "fabric": "cotton",
    "textile": "cotton",
    "cloth": "cotton",
    "denim": "cotton",
    "canvas": "cotton",
    "linen": "jute",
    "hemp": "jute",
    "granite": "stone",
    "marble": "stone",
    "slate": "stone",
    "chrome": "stainless_steel",
    "chromium": "stainless_steel",
    "bronze": "brass",
    "gold": "copper",
    "silver": "copper",
    "platinum": "nickel",
    "tungsten": "nickel",
    "fibre_glass": "fiberglass",
    "fiber_glass": "fiberglass",
    "cf": "carbon_fiber",
    "cfrp": "carbon_fiber",
    "gfrp": "fiberglass",
    "battery": "lithium_ion_battery",
    "li_ion": "lithium_ion_battery",
    "lithium": "lithium_ion_battery",
}

# ---------------------------------------------------------------------------
# Manufacturing factors (kg CO2e / kg of product, by product category)
# ---------------------------------------------------------------------------
MANUFACTURING_FACTORS: dict[str, float] = {
    "electronics": 3.0,
    "appliances": 2.0,
    "furniture": 1.0,
    "clothing": 2.5,
    "toys": 1.5,
    "automotive": 2.5,
    "sports": 1.5,
    "kitchen": 1.8,
    "tools": 2.0,
    "beauty": 1.0,
    "office": 1.2,
    "garden": 1.2,
    "pet": 1.0,
    "default": 1.5,
}

# ---------------------------------------------------------------------------
# Transportation factor
# ---------------------------------------------------------------------------
TRANSPORT_FACTOR = 0.1  # kg CO2e per kg per 1000 km
DEFAULT_TRANSPORT_DISTANCE_KKM = 5.0  # 5000 km expressed in units of 1000 km

# ---------------------------------------------------------------------------
# Use-phase factors (kg CO2e / kg / year)
# ---------------------------------------------------------------------------
USE_PHASE_FACTORS: dict[str, float] = {
    "electronics": 2.0,
    "appliances": 3.0,
    "default": 0.1,
}
DEFAULT_PRODUCT_LIFETIME_YEARS = 5

# ---------------------------------------------------------------------------
# End-of-life disposal method factors (kg CO2e / kg)
# ---------------------------------------------------------------------------
EOL_METHOD_FACTORS: dict[str, float] = {
    "landfill": 0.5,
    "incineration": 1.0,
    "recycling": -0.3,
}

# ---------------------------------------------------------------------------
# End-of-life disposal scenarios (method -> fraction)
# ---------------------------------------------------------------------------
EOL_SCENARIOS: dict[str, dict[str, float]] = {
    "baseline": {"landfill": 0.6, "incineration": 0.2, "recycling": 0.2},
    "best_case": {"landfill": 0.1, "incineration": 0.1, "recycling": 0.8},
    "worst_case": {"landfill": 0.8, "incineration": 0.2, "recycling": 0.0},
}

# ---------------------------------------------------------------------------
# Valid product categories (for validation)
# ---------------------------------------------------------------------------
VALID_CATEGORIES = list(MANUFACTURING_FACTORS.keys())
