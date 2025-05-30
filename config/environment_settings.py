from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProjectSettings(BaseSettings):
    bot_token: str = Field(alias="bot_token")
    debug_mode: bool = Field(alias="debug_mode")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")
