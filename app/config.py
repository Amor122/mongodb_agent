from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017/mydb"
    MONGODB_DB_NAME: str = "mydb"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
