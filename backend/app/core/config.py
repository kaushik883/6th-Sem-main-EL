from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "FreightAudit Pro API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Auth
    JWT_SECRET: str = "your-secret-key-here"  # Override in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/freightaudit"
    
    # APIs
    VERYFI_CLIENT_ID: str = ""
    VERYFI_CLIENT_SECRET: str = ""
    VERYFI_USERNAME: str = ""
    VERYFI_API_KEY: str = ""
    
    OPENAI_API_KEY: str = ""
    # Cloudflare R2
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
