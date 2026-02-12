"""
Product Fetcher — Uses Rainforest API to fetch Amazon product data by ASIN.
Returns a combined description string suitable for LLM parsing.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.rainforestapi.com/request"


class ProductFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def fetch_product(self, asin: str, amazon_domain: str = "amazon.com") -> str:
        """
        Fetch product data from Rainforest API and return a combined description string.

        Concatenates title, description, feature bullets, and specifications
        into a single text block for the LLM to parse.
        """
        params = {
            "api_key": self.api_key,
            "type": "product",
            "amazon_domain": amazon_domain,
            "asin": asin,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(BASE_URL, params=params)

        if response.status_code != 200:
            logger.error(f"Rainforest API error {response.status_code}: {response.text[:500]}")
            raise RuntimeError(f"Rainforest API returned status {response.status_code}")

        data = response.json()
        product = data.get("product", {})

        if not product:
            raise ValueError(f"No product data found for ASIN {asin}")

        # Build combined description from all available fields
        parts: list[str] = []

        title = product.get("title", "")
        if title:
            parts.append(f"Product: {title}")

        description = product.get("description", "")
        if description:
            parts.append(f"Description: {description}")

        bullets = product.get("feature_bullets", [])
        if bullets:
            parts.append("Features:\n" + "\n".join(f"- {b}" for b in bullets))

        specs = product.get("specifications", [])
        if specs:
            spec_lines = [f"- {s['name']}: {s['value']}" for s in specs if "name" in s and "value" in s]
            if spec_lines:
                parts.append("Specifications:\n" + "\n".join(spec_lines))

        weight = product.get("weight")
        if weight:
            parts.append(f"Weight: {weight}")

        dimensions = product.get("dimensions")
        if dimensions:
            parts.append(f"Dimensions: {dimensions}")

        combined = "\n\n".join(parts)

        if not combined.strip():
            raise ValueError(f"Rainforest API returned empty product data for ASIN {asin}")

        logger.info(f"Fetched product data for {asin}: {len(combined)} chars")
        return combined
