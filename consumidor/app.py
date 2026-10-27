"""Processo principal: MQTT (paho 2.x) -> MongoDB, pensado para rodar 48h+ sem supervisao."""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from logging.handlers import RotatingFileHandler

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from pymongo import MongoClient

from .config import Config, carregar
from .nucleo import Armazenamento

log = logging.getLogger("consumidor")


def configurar_log(cfg: Config) -> None:
    os.makedirs(cfg.log_dir, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    raiz = logging.getLogger()
    raiz.setLevel(cfg.log_level)
    arq = RotatingFileHandler(os.path.join(cfg.log_dir, "consumidor.log"),
                              maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    out = logging.StreamHandler(sys.stdout)
    for h in (arq, out):
        h.setFormatter(fmt)
        raiz.addHandler(h)
    logging.getLogger("pymongo").setLevel(logging.WARNING)


def criar_cliente_mqtt(cfg: Config, armaz: Armazenamento) -> mqtt.Client:
    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cfg.mqtt_client_id,
                      clean_session=False)  # sessao persistente: broker guarda QoS1 durante quedas curtas
    if cfg.mqtt_user:
        cli.username_pw_set(cfg.mqtt_user, cfg.mqtt_password)
    if cfg.mqtt_tls:
        cli.tls_set()
    cli.reconnect_delay_set(min_delay=1, max_delay=60)

    def on_connect(c, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("Broker recusou a conexao: %s", reason_code)
            return
        log.info("Conectado ao broker (%s); assinando %s", cfg.mqtt_host, cfg.mqtt_topic)
        c.subscribe(cfg.mqtt_topic, qos=1)  # re-subscribe a cada (re)conexao

    def on_disconnect(c, userdata, disconnect_flags, reason_code, properties):
        log.warning("Desconectado do broker (%s); reconexao automatica", reason_code)

    def on_message(c, userdata, msg):
        try:
            armaz.tratar_mensagem(msg.topic, msg.payload)
        except Exception:  # nunca derrubar o loop de rede
            log.exception("Erro inesperado ao tratar mensagem em %s", msg.topic)

    cli.on_connect = on_connect
    cli.on_disconnect = on_disconnect
    cli.on_message = on_message
    return cli


def main() -> int:
    load_dotenv()
    cfg = carregar()
    configurar_log(cfg)
    log.info("Iniciando consumidor: %s", cfg.resumo())

    mongo = MongoClient(cfg.mongo_uri, serverSelectionTimeoutMS=5000, retryWrites=True)
    armaz = Armazenamento(mongo[cfg.mongo_db][cfg.mongo_collection], buffer_max=cfg.buffer_max)
    armaz.criar_indices()  # se falhar, a manutencao tenta de novo

    parar = threading.Event()

    def sinal(signum, frame):
        log.info("Sinal %s recebido; encerrando", signum)
        parar.set()

    signal.signal(signal.SIGINT, sinal)
    signal.signal(signal.SIGTERM, sinal)

    cli = criar_cliente_mqtt(cfg, armaz)
    cli.connect_async(cfg.mqtt_host, cfg.mqtt_port, keepalive=60)  # tenta de novo sozinho se o broker estiver fora
    cli.loop_start()

    while not parar.wait(cfg.heartbeat_segundos):
        armaz.manutencao()
        log.info("HEARTBEAT mqtt_conectado=%s %s", cli.is_connected(), armaz.estatisticas())

    cli.disconnect()
    cli.loop_stop()
    armaz.manutencao()  # ultima tentativa de esvaziar o buffer
    log.info("FINAL %s", armaz.estatisticas())
    mongo.close()
    return 0
