"""
EcoFlow LCA — FastAPI Application
Endpoints:
  GET /health           → Health check
  GET /analyze/{asin}   → LCA analysis with cache-aside pattern
"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from upstash_redis import Redis

from config import settings
from services.llm import LLMService
from services.product_fetcher import ProductFetcher
from services.calculator import calculate_lca

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Service singletons (initialized on startup)
# ---------------------------------------------------------------------------
llm_service: LLMService | None = None
product_fetcher: ProductFetcher | None = None
redis_client: Redis | None = None
supabase_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services once during application startup."""
    global llm_service, product_fetcher, redis_client, supabase_client

    # LLM Service
    if settings.anthropic_api_key:
        llm_service = LLMService(api_key=settings.anthropic_api_key)
        logger.info("Anthropic LLM service initialized")
    else:
        logger.warning("ANTHROPIC_API_KEY not set — LLM service unavailable")

    # Product Fetcher (Rainforest API)
    if settings.rainforest_api_key:
        product_fetcher = ProductFetcher(api_key=settings.rainforest_api_key)
        logger.info("Rainforest product fetcher initialized")
    else:
        logger.warning("RAINFOREST_API_KEY not set — auto-fetch disabled")

    # Redis
    if settings.upstash_redis_url and settings.upstash_redis_token:
        redis_client = Redis(
            url=settings.upstash_redis_url,
            token=settings.upstash_redis_token,
        )
        logger.info("Upstash Redis connected")
    else:
        logger.warning("Redis credentials not set — caching disabled")

    # Supabase
    if settings.supabase_url and settings.supabase_key:
        from supabase import create_client
        supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client initialized")
    else:
        logger.warning("Supabase credentials not set — persistence disabled")

    yield

    logger.info("Shutting down EcoFlow LCA")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="EcoFlow LCA",
    description="Life Cycle Assessment API for Amazon products",
    version="1.0.0",
    lifespan=lifespan,
)

_allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if settings.frontend_url:
    _allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ecoflow-lca"}


@app.get("/analyze/{asin}")
async def analyze(
    asin: str,
    description: str | None = Query(None, description="Product description text (optional — auto-fetched from Amazon if omitted)"),
    eol_scenario: str = Query("baseline", description="EOL scenario: baseline, best_case, worst_case"),
):
    """
    Analyze a product's lifecycle environmental impact.

    Cache-aside pattern:
      1. Check Redis cache
      2. Check Supabase persistent store
      3. Fetch product data (Rainforest API or provided description)
      4. Compute via LLM + Calculator
      5. Write back to Redis + Supabase
    """
    cache_key = f"lca:{asin}"

    # --- Layer 1: Redis cache ----------------------------------------------
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"Cache HIT for {asin}")
                data = json.loads(cached) if isinstance(cached, str) else cached
                return data
        except Exception as e:
            logger.warning(f"Redis read error: {e}")

    # --- Layer 2: Supabase persistent store --------------------------------
    if supabase_client:
        try:
            row = (
                supabase_client.table("analyses")
                .select("result")
                .eq("asin", asin)
                .execute()
            )
            if row.data:
                result = row.data[0]["result"]
                logger.info(f"Supabase HIT for {asin}")
                # Backfill Redis cache
                if redis_client:
                    try:
                        redis_client.setex(cache_key, 86400, json.dumps(result))
                    except Exception:
                        pass
                return result
        except Exception as e:
            logger.warning(f"Supabase read error: {e}")

    # --- Resolve product description ---------------------------------------
    if not description:
        if not product_fetcher:
            raise HTTPException(
                status_code=503,
                detail="No description provided and Rainforest API not configured. Set RAINFOREST_API_KEY or provide a description.",
            )
        try:
            description = await product_fetcher.fetch_product(asin)
        except Exception as e:
            logger.error(f"Product fetch failed for {asin}: {e}")
            raise HTTPException(status_code=502, detail=f"Failed to fetch product data: {str(e)}")

    # --- Layer 3: Compute --------------------------------------------------
    if not llm_service:
        raise HTTPException(
            status_code=503,
            detail="LLM service unavailable. Set ANTHROPIC_API_KEY.",
        )

    try:
        parsed = await llm_service.parse_product(description)
    except Exception as e:
        logger.error(f"LLM parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM parsing error: {str(e)}")

    try:
        lca_result = calculate_lca(parsed, eol_scenario=eol_scenario)
    except Exception as e:
        logger.error(f"LCA calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")

    result = lca_result.model_dump()

    # --- Write-back to cache and persistence -------------------------------
    result_json = json.dumps(result)

    if redis_client:
        try:
            redis_client.setex(cache_key, 86400, result_json)
            logger.info(f"Cached result for {asin} (TTL=24h)")
        except Exception as e:
            logger.warning(f"Redis write error: {e}")

    if supabase_client:
        try:
            supabase_client.table("analyses").insert({
                "asin": asin,
                "result": result,
                "description": description[:2000],
            }).execute()
            logger.info(f"Stored result for {asin} in Supabase")
        except Exception as e:
            logger.warning(f"Supabase write error: {e}")

    return result
