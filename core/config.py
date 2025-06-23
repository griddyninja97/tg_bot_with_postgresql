from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field  

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    url: str = Field(..., env="URL")  
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid"
    )

settings = Settings()
