import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = os.getenv("ENV", "development")

    # ----------------------------------
    # DB Settings
    # ----------------------------------
    SQLALCHEMY_DATABASE_URI: str = (
        "mysql+pymysql://user:password@localhost/mydb"
        if ENV == "production"
        else "sqlite:///appsavi.db"
    )

    JWT_SECRET_KEY: str = "SUPERSECRETKEY"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # External Zitadel
    ZITADEL_DOMAIN: str = "https://id.appsavi.com"
    ZITADEL_CLIENT_ID: str = "python2"
    ZITADEL_CLIENT_SECRET: str = "m11hxwbYUPQUBkIZltJUsBCzCqcCbyU2jjPcprgEvby7nUDpnvM8VEVo6ioSv2yb"


settings = Settings()
