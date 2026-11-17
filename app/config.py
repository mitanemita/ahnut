"""Настройки из переменных окружения (.env на сервере). Секретов в коде нет."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_user: str = "ahnut"
    db_password: str = "ahnut"
    db_name: str = "ahnut"
    db_host: str = "localhost"
    db_port: int = 5432
    # Полный URL перекрывает поля выше (например, sqlite в тестах)
    database_url: str | None = None

    public_base_url: str = "https://ahnut.ru"

    @property
    def dsn(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
