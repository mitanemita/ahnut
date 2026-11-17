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

    # --- ЮKassa ---
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_api_url: str = "https://api.yookassa.ru/v3"
    # Принимать уведомления только с IP ЮKassa (за Caddy реальный IP берётся из X-Forwarded-For)
    yookassa_check_ip: bool = True

    # --- Внутренний конвейер (n8n ↔ web) ---
    internal_token: str = ""  # общий секрет: n8n передаёт его в заголовке X-Internal-Token
    n8n_generate_url: str = ""  # внутренний вебхук n8n, напр. http://n8n:5678/webhook/generate

    # --- Нейросеть: одна точка доступа, провайдер меняется через .env ---
    # OpenRouter: LLM_BASE_URL=https://openrouter.ai/api ; прямой API: https://api.anthropic.com
    llm_base_url: str = "https://openrouter.ai/api"
    llm_api_key: str = ""
    llm_model_zapiska: str = "anthropic/claude-opus-5.5"
    llm_model_svidanie: str = "anthropic/claude-opus-5.5"
    llm_model_prince: str = "anthropic/claude-opus-5.5"
    # false — если провайдер не поддерживает structured outputs (тогда JSON проверяется после ответа)
    llm_structured: bool = True
    # Только для разработки: «нейросеть» без сети, подставляет ответы анкеты в шаблон
    llm_fake: bool = False

    # Файлы фото и открыток на диске сервера
    files_dir: str = "data/files"

    @property
    def dsn(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
