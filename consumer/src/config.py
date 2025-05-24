from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class KafkaConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="CONSUMER_") 

    KAFKA_BOOTSTRAP_SERVERS: str
    SCHEMA_REGISTRY_SERVER: str
    KAFKA_TOPIC_ORDERS: str
    KAFKA_TOPIC_USERS: str
    GROUP_ID: str
    POLL_INTERVAL_SECONDS: int