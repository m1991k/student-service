from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME:str="Student Service"
    DEBUG:bool=False
    MONGO_URI:str
    MONGO_DB:str

    class Config:
        env_file=".env"

settings=Settings()
