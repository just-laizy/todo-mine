from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field

class Settings  (BaseSettings):
    # db_url : str
    JWT_SECRET : str
    JWT_ALGORITHM : str =  "HS256"   
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 1440
    model_config = SettingsConfigDict(env_file='.env',extra="ignore")
    REDIS_URL: str
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    
    DB_SCHEMA:str
    DB_USER:str
    DB_HOST:str 
    DB_PORT:int
    DB_PASSWORD:str
    DB_NAME:str

    
    @computed_field
    @property
    def database_url(self) -> str:
        return f"{self.DB_SCHEMA}+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?ssl_disabled=true"
        # db_url = "mysql+pymysql://root:12345@localhost:3306/todo"
    

settings = Settings() # type: ignore