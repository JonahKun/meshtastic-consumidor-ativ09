import importlib.util
import json
import os
from types import SimpleNamespace

import mongomock

from consumidor.app import criar_cliente_mqtt
from consumidor.config import carregar
from consumidor.nucleo import Armazenamento

caminho = os.path.join(os.path.dirname(__file__), "..", "ferramentas", "simulador.py")
spec = importlib.util.spec_from_file_location("simulador", caminho)
sim = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sim)


def test_simulador_gera_variedade_e_tudo_e_gravado():
    col = mongomock.MongoClient()["t"]["pacotes_brutos"]
    a = Armazenamento(col)
    msgs = sim.gerar_rodada()
    for top, payload in msgs:
        assert top.startswith("msh/SIMULADO/2/json/")
        a.tratar_mensagem(top, payload)
    assert col.count_documents({}) == len(msgs)      # nada descartado
    assert a.json_invalido == 2                      # JSON quebrado + vazio
    tipos = {d["mensagem"].get("type") for d in col.find({"mensagem": {"$exists": True}})}
    assert {"telemetry", "position", "nodeinfo", "text"} <= tipos
    pares = [(d["mensagem"]["from"], d["mensagem"]["id"]) for d in col.find({"mensagem.from": {"$exists": True}})]
    assert len(pares) != len(set(pares))             # ha duplicatas from+id


def test_simulador_recusa_host_remoto(monkeypatch):
    monkeypatch.setattr("sys.argv", ["simulador.py", "--host", "broker.exemplo.invalido"])
    assert sim.main() == 2


def test_callbacks_mqtt_resubscribe_e_mensagem():
    col = mongomock.MongoClient()["t"]["pacotes_brutos"]
    a = Armazenamento(col)
    cfg = carregar({"MQTT_USER": "u", "MQTT_PASSWORD": "p", "MQTT_CLIENT_ID": "x"})
    cli = criar_cliente_mqtt(cfg, a)
    assinaturas = []
    fake = SimpleNamespace(subscribe=lambda t, qos=0: assinaturas.append((t, qos)))
    ok = SimpleNamespace(is_failure=False)
    cli.on_connect(fake, None, {}, ok, None)
    cli.on_connect(fake, None, {}, ok, None)  # reconexao => assina de novo
    assert assinaturas == [("msh/+/2/json/#", 1)] * 2
    cli.on_message(fake, None, SimpleNamespace(topic="msh/X/2/json/c/!1", payload=json.dumps({"id": 1}).encode()))
    assert col.count_documents({}) == 1
