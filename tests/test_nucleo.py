import json
from datetime import datetime, timedelta, timezone

import mongomock
import pytest
from pymongo.errors import ServerSelectionTimeoutError

from consumidor.config import carregar, mascarar_uri
from consumidor.nucleo import Armazenamento, montar_documento

TOPICO = "msh/BR_902/2/json/LongFast/!a1b2c3d4"
PACOTE = {"channel": 0, "from": 305419896, "id": 1234567, "payload": {"battery_level": 87, "voltage": 4.1},
          "rssi": -95, "sender": "!a1b2c3d4", "snr": 5.5, "timestamp": 1790000000, "to": -1,
          "type": "telemetry", "hops_away": 1}


@pytest.fixture
def col():
    return mongomock.MongoClient()["t"]["pacotes_brutos"]


@pytest.fixture
def armaz(col):
    return Armazenamento(col, buffer_max=5)


def test_json_valido_grava_sem_transformar(armaz, col):
    bruto = json.dumps(PACOTE).encode()
    armaz.tratar_mensagem(TOPICO, bruto)
    doc = col.find_one()
    assert set(doc) == {"_id", "topico", "recebido_em", "mensagem"}
    assert doc["topico"] == TOPICO
    assert doc["mensagem"] == PACOTE
    assert isinstance(doc["recebido_em"], datetime)


def test_recebido_em_utc_recente(armaz):
    doc = armaz.tratar_mensagem(TOPICO, b"{}")
    assert doc["recebido_em"].tzinfo == timezone.utc
    assert abs(datetime.now(timezone.utc) - doc["recebido_em"]) < timedelta(seconds=5)


@pytest.mark.parametrize("payload", [b"", b"nao e json", b'{"a": ', b"\xff\xfe\x00lixo"])
def test_json_invalido_vai_para_mensagem_raw(armaz, col, payload):
    armaz.tratar_mensagem(TOPICO, payload)
    doc = col.find_one()
    assert "mensagem" not in doc
    assert isinstance(doc["mensagem_raw"], str)
    assert doc["topico"] == TOPICO
    assert armaz.json_invalido == 1 and armaz.gravadas == 1


def test_json_nao_objeto_tambem_e_guardado(armaz, col):
    armaz.tratar_mensagem(TOPICO, b"[1, 2, 3]")
    assert col.find_one()["mensagem"] == [1, 2, 3]


def test_duplicatas_nao_sao_removidas(armaz, col):
    for _ in range(3):
        armaz.tratar_mensagem(TOPICO, json.dumps(PACOTE).encode())
    assert col.count_documents({}) == 3


def test_indices(armaz, col):
    assert armaz.criar_indices()
    info = col.index_information()
    chaves = [tuple(k for k, _ in v["key"]) for v in info.values()]
    assert ("recebido_em",) in chaves
    assert ("mensagem.from", "mensagem.id") in chaves
    assert not any(v.get("unique") for k, v in info.items() if k != "_id_")


class ColecaoQueFalha:
    """Envolve uma colecao e simula queda do Mongo."""

    def __init__(self, real):
        self.real = real
        self.fora = False

    def insert_one(self, d):
        if self.fora:
            raise ServerSelectionTimeoutError("fora")
        return self.real.insert_one(d)

    def insert_many(self, ds, ordered=True):
        if self.fora:
            raise ServerSelectionTimeoutError("fora")
        return self.real.insert_many(ds, ordered=ordered)

    def create_index(self, *a, **k):
        if self.fora:
            raise ServerSelectionTimeoutError("fora")
        return self.real.create_index(*a, **k)


def test_buffer_quando_mongo_cai_e_reenvio(col):
    c = ColecaoQueFalha(col)
    a = Armazenamento(c, buffer_max=5)
    a.tratar_mensagem(TOPICO, b'{"id": 1}')
    c.fora = True
    a.tratar_mensagem(TOPICO, b'{"id": 2}')
    a.tratar_mensagem(TOPICO, b'{"id": 3}')
    assert len(a.buffer) == 2 and a.falhas >= 1 and col.count_documents({}) == 1
    c.fora = False
    a.tratar_mensagem(TOPICO, b'{"id": 4}')  # reenvia pendentes antes, em ordem
    assert [d["mensagem"]["id"] for d in col.find()] == [1, 2, 3, 4]
    assert len(a.buffer) == 0 and a.gravadas == 4 and a.recebidas == 4


def test_manutencao_esvazia_buffer_e_recria_indices(col):
    c = ColecaoQueFalha(col)
    a = Armazenamento(c, buffer_max=5)
    c.fora = True
    assert not a.criar_indices()
    a.tratar_mensagem(TOPICO, b'{"id": 1}')
    c.fora = False
    a.manutencao()
    assert col.count_documents({}) == 1 and a.indices_ok


def test_buffer_limitado_descarta_mais_antigo_e_conta(col):
    c = ColecaoQueFalha(col)
    c.fora = True
    a = Armazenamento(c, buffer_max=3)
    for i in range(5):
        a.tratar_mensagem(TOPICO, json.dumps({"id": i}).encode())
    assert len(a.buffer) == 3 and a.descartadas == 2
    assert [d["mensagem"]["id"] for d in a.buffer] == [2, 3, 4]


def test_inteiro_gigante_nao_e_perdido(armaz, col):
    armaz.tratar_mensagem(TOPICO, b'{"id": 123456789012345678901234567890}')
    doc = col.find_one()
    assert doc is not None  # mongomock aceita ou cai em mensagem_raw; nunca descarta
    assert armaz.gravadas == 1


def test_montar_documento_bytes_e_str():
    d1 = montar_documento("t", b'{"a": 1}')
    d2 = montar_documento("t", '{"a": 1}')
    assert d1["mensagem"] == d2["mensagem"] == {"a": 1}


def test_config_defaults_e_sem_vazar_senha():
    cfg = carregar({"MQTT_HOST": "h", "MQTT_PASSWORD": "segredo123",
                    "MONGO_URI": "mongodb://u:segredo456@m:27017/?authSource=admin"})
    assert cfg.mqtt_topic == "msh/+/2/json/#"
    assert cfg.mongo_collection == "pacotes_brutos"
    assert cfg.mqtt_port == 1883
    texto = cfg.resumo() + repr(cfg)
    assert "segredo123" not in texto and "segredo456" not in texto
    assert mascarar_uri("mongodb://u:p@h/") == "mongodb://u:***@h/"
    assert carregar({"MQTT_TLS": "true"}).mqtt_port == 8883
