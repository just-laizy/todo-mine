from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings  (BaseSettings):
    db_url : str
    JWT_SECRET : str
    JWT_ALGORITHM : str =  "HS256"   
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 1440
    model_config = SettingsConfigDict(env_file='.env')
    REDIS_URL: str

settings = Settings() # type: ignore