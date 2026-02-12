from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_key: str = ""
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
