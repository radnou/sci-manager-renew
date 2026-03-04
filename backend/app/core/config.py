from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    supabase_url: AnyUrl
    supabase_key: str
    stripe_secret_key: str
    stripe_publishable_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    return Settings()
