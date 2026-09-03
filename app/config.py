from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "BHASHA SETU"
    environment: str = Field(default="development")
    allowed_origins: list[str] = ["*"]

    model_config = ConfigDict(env_file=".env")


settings = Settings()
