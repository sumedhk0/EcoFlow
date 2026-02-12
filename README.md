# EcoFlow LCA

Life Cycle Assessment (LCA) web application for Amazon products. Analyzes environmental impact from cradle to grave using AI-powered material extraction and scientific emission factors.

## Architecture

- **Backend**: FastAPI (Python 3.11) — LLM-powered product parsing, LCA calculations, Redis caching, Supabase persistence
- **Frontend**: Next.js 15 (TypeScript/Tailwind) — Interactive Sankey diagram with What-If disposal scenarios
- **LLM**: Claude API (Anthropic) for structured material extraction
- **Cache**: Upstash Redis (cache-aside pattern, 24h TTL)
- **Database**: Supabase (PostgreSQL) for persistent analysis storage

## Prerequisites

- Python 3.11+ and Node.js 22+ (for local dev), **or** Docker
- API keys for: Anthropic, Upstash Redis, Supabase

## External Service Setup

### Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run this SQL in the SQL Editor to create the `analyses` table:

```sql
CREATE TABLE analyses (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  asin TEXT NOT NULL,
  description TEXT,
  result JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_analyses_asin ON analyses (asin);
```

3. Copy your **Project URL** and **anon key** from Settings > API

### Upstash Redis

1. Create a database at [upstash.com](https://upstash.com)
2. Copy the **REST URL** and **REST Token** from the database details

### Anthropic API

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)

## Configuration

Copy the example env file and fill in your credentials:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
UPSTASH_REDIS_URL=https://your-db.upstash.io
UPSTASH_REDIS_TOKEN=your-token
ANTHROPIC_API_KEY=sk-ant-...
RAINFOREST_API_KEY=your-anon-key
```

## Running with Docker

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## API

### `GET /analyze/{asin}?description=...&eol_scenario=baseline`

Analyzes a product and returns Sankey diagram data.

**Parameters:**
- `asin` (path) — Amazon product identifier
- `description` (query, required) — Product description text
- `eol_scenario` (query, optional) — `baseline`, `best_case`, or `worst_case`

**Response:** JSON with `nodes`, `links`, `summary`, `per_material_weights`, `material_details`

### `GET /health`

Returns `{"status": "ok"}`.

## LCA Methodology

Five lifecycle phases are assessed:

| Phase | Formula |
|-------|---------|
| Raw Material Extraction | `sum(material_weight * emission_factor)` |
| Manufacturing | `total_weight * category_factor` |
| Transportation | `total_weight * 0.1 * 5` (5000km default) |
| Use Phase | `total_weight * use_factor * 5` (5yr lifetime) |
| End of Life | `sum(material_weight * blended_disposal_factor)` |

Emission factors sourced from ecoinvent, EPA WARM, and peer-reviewed literature. 50 materials covered across plastics, metals, natural/organic, minerals, and paper categories.
