from pydantic_settings import BaseSettings, SettingsConfigDict


class MinioTestSettings(BaseSettings):
    MINIO_ENDPOINT_TEST: str
    MINIO_ACCESS_KEY_TEST: str
    MINIO_SECRET_KEY_TEST: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


minio_settings = MinioTestSettings()
