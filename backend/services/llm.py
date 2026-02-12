"""
LLM Service — Uses Claude API (Anthropic SDK) to parse Amazon product
descriptions into structured material composition data.
"""

import json
import logging

import anthropic
from pydantic import BaseModel
from thefuzz import process as fuzz_process

from data.emission_factors import MATERIAL_FACTORS, MATERIAL_ALIASES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ProductParsed(BaseModel):
    materials: dict[str, float]  # canonical_name -> fraction (sums to 1.0)
    weight_kg: float
    category: str


# ---------------------------------------------------------------------------
# Tool schema for structured output via Claude tool use
# ---------------------------------------------------------------------------

EXTRACT_TOOL = {
    "name": "extract_product_info",
    "description": "Extract material composition, weight, and category from a product description.",
    "input_schema": {
        "type": "object",
        "properties": {
            "materials": {
                "type": "object",
                "description": (
                    "Map of material names to their mass fraction of the product. "
                    "Fractions must sum to 1.0. Use specific material names like "
                    "'steel', 'abs', 'polycarbonate', 'cotton', 'aluminum', etc."
                ),
                "additionalProperties": {"type": "number"},
            },
            "weight_kg": {
                "type": "number",
                "description": "Estimated total product weight in kilograms.",
            },
            "category": {
                "type": "string",
                "description": (
                    "Product category. Must be one of: electronics, appliances, "
                    "furniture, clothing, toys, automotive, sports, kitchen, "
                    "tools, beauty, office, garden, pet, default."
                ),
                "enum": [
                    "electronics", "appliances", "furniture", "clothing",
                    "toys", "automotive", "sports", "kitchen", "tools",
                    "beauty", "office", "garden", "pet", "default",
                ],
            },
        },
        "required": ["materials", "weight_kg", "category"],
    },
}

SYSTEM_PROMPT = """You are a materials science expert. Given an Amazon product description,
analyze the product and extract:
1. The material composition as mass fractions (must sum to 1.0)
2. The estimated total weight in kilograms
3. The product category

Use specific material names like: steel, stainless_steel, aluminum, copper, abs,
polycarbonate, hdpe, pp, pet, nylon, cotton, leather, wood, glass, cardboard, etc.

Be precise with weight estimates based on the product type and size.
If materials are not explicitly stated, infer them from the product type."""


# ---------------------------------------------------------------------------
# LLM Service class
# ---------------------------------------------------------------------------


class LLMService:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    async def parse_product(self, description: str) -> ProductParsed:
        """Parse a product description into structured material data."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "extract_product_info"},
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this Amazon product and extract its material composition:\n\n{description}",
                }
            ],
        )

        # Extract the tool call result
        tool_input = None
        for block in response.content:
            if block.type == "tool_use" and block.name == "extract_product_info":
                tool_input = block.input
                break

        if tool_input is None:
            raise ValueError("LLM did not return structured tool output")

        # Validate and normalize
        raw_materials: dict = tool_input.get("materials", {})
        weight_kg: float = float(tool_input.get("weight_kg", 1.0))
        category: str = tool_input.get("category", "default").lower()

        # Normalize material names and fractions
        normalized = self._normalize_materials(raw_materials)

        return ProductParsed(
            materials=normalized,
            weight_kg=max(weight_kg, 0.01),  # floor at 10g
            category=category,
        )

    def _normalize_materials(self, raw: dict[str, float]) -> dict[str, float]:
        """
        Three-layer normalization:
        1. Resolve aliases (exact match)
        2. Fuzzy-match against canonical keys (threshold 70)
        3. Normalize fractions to sum to 1.0
        """
        canonical_keys = list(MATERIAL_FACTORS.keys())
        resolved: dict[str, float] = {}

        for name, fraction in raw.items():
            key = name.lower().strip().replace(" ", "_").replace("-", "_")

            # Layer 1: direct match in canonical or alias
            if key in MATERIAL_FACTORS:
                canonical = key
            elif key in MATERIAL_ALIASES:
                canonical = MATERIAL_ALIASES[key]
            else:
                # Layer 2: fuzzy match
                match = fuzz_process.extractOne(key, canonical_keys, score_cutoff=70)
                if match:
                    canonical = match[0]
                    logger.info(f"Fuzzy matched '{key}' -> '{canonical}' (score={match[1]})")
                else:
                    canonical = key  # keep as-is, will use default factor
                    logger.warning(f"No match for material '{key}', using default factor")

            # Accumulate fractions for same canonical material
            resolved[canonical] = resolved.get(canonical, 0.0) + fraction

        # Layer 3: normalize fractions to sum to 1.0
        total = sum(resolved.values())
        if total > 0 and abs(total - 1.0) > 0.01:
            logger.info(f"Normalizing material fractions from {total:.3f} to 1.0")
            resolved = {k: v / total for k, v in resolved.items()}

        return resolved
