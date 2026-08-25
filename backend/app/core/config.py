from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MySQL
    database_url: str

    # JWT
    secret_key: str
    access_token_expire_minutes: int = 30

    # AWS
    aws_region: str = "ap-south-1"
    aws_profile: str | None = None
        # Frontend
    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()