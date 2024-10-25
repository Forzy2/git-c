import os
import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Secret



BASE_DIR = pathlib.Path(os.path.dirname(__file__))

OWN_USER_ID = [1444076771]
TIME = 21


class Settings(BaseSettings):
    TOKEN: SecretStr
    
    model_config = SettingsConfigDict(env_file=BASE_DIR / 'assets/configs/.env', env_file_encoding='utf-8')

config = Settings()