"""Configuracao lida de variaveis de ambiente / .env. Segredos nunca sao logados."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass


def _bool(valor: str | None, padrao: bool = False) -> bool:
    if valor is None or valor.strip() == "":
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "sim", "on")


def mascarar_uri(uri: str) -> str:
    """Troca a senha de uma URI (user:senha@host) por ***."""
    return re.sub(r"(://[^:/@]+:)[^@]*(@)", r"\1***\2", uri)


@dataclass
class Config:
    mqtt_host: str
    mqtt_port: int
    mqtt_user: str
    mqtt_password: str
    mqtt_tls: bool
    mqtt_topic: str
    mqtt_client_id: str
    mongo_uri: str
    mongo_db: str
    mongo_collection: str
    log_dir: str = "logs"
    log_level: str = "INFO"
    heartbeat_segundos: int = 60
    buffer_max: int = 10000

    def resumo(self) -> str:
        """Texto seguro para log (sem senhas)."""
        return (
            f"mqtt={self.mqtt_host}:{self.mqtt_port} tls={self.mqtt_tls} "
            f"usuario={self.mqtt_user or '(anonimo)'} topico={self.mqtt_topic} "
            f"client_id={self.mqtt_client_id} mongo={mascarar_uri(self.mongo_uri)} "
            f"db={self.mongo_db} colecao={self.mongo_collection} buffer_max={self.buffer_max}"
        )

    def __repr__(self) -> str:  # evita vazar senha por acidente
        return f"Config({self.resumo()})"


def carregar(env: dict | None = None) -> Config:
    env = os.environ if env is None else env
    tls = _bool(env.get("MQTT_TLS"))
    return Config(
        mqtt_host=env.get("MQTT_HOST", "localhost"),
        mqtt_port=int(env.get("MQTT_PORT") or (8883 if tls else 1883)),
        mqtt_user=env.get("MQTT_USER", ""),
        mqtt_password=env.get("MQTT_PASSWORD", ""),
        mqtt_tls=tls,
        mqtt_topic=env.get("MQTT_TOPIC") or "msh/+/2/json/#",
        mqtt_client_id=env.get("MQTT_CLIENT_ID", "consumidor-pacotes-brutos"),
        mongo_uri=env.get("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db=env.get("MONGO_DB", "meshtastic"),
        mongo_collection=env.get("MONGO_COLLECTION") or "pacotes_brutos",
        log_dir=env.get("LOG_DIR", "logs"),
        log_level=env.get("LOG_LEVEL", "INFO").upper(),
        heartbeat_segundos=int(env.get("HEARTBEAT_SEGUNDOS") or 60),
        buffer_max=int(env.get("BUFFER_MAX") or 10000),
    )
