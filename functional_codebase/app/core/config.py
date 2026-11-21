from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str = "rbpdb"
    postgres_password: str = "rbpdb"
    postgres_db: str = "rbpdb"
    db_host: str = "localhost"
    db_port: int = 5432
    database_url: str = ""

    @model_validator(mode="after")
    def set_database_url(self) -> "Settings":
        if not self.database_url:
            self.database_url = URL.create(
                drivername="postgresql+psycopg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.db_host,
                port=self.db_port,
                database=self.postgres_db,
            ).render_as_string(hide_password=False)
        return self


settings = Settings()
