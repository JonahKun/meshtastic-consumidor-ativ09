import importlib.util
import os
from datetime import datetime, timedelta, timezone

import mongomock

caminho = os.path.join(os.path.dirname(__file__), "..", "consultas", "contagem_por_no_48h.py")
spec = importlib.util.spec_from_file_location("contagem", caminho)
contagem = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contagem)


def test_contagem_por_no_e_salto():
    col = mongomock.MongoClient()["t"]["pacotes_brutos"]
    agora = datetime.now(timezone.utc)
    docs = [
        {"recebido_em": agora - timedelta(hours=1), "mensagem": {"from": 1, "id": 1, "hops_away": 0}},
        {"recebido_em": agora - timedelta(hours=2), "mensagem": {"from": 1, "id": 2, "hops_away": 0}},
        {"recebido_em": agora - timedelta(hours=3), "mensagem": {"from": 2, "id": 3, "hops_away": 2}},
        {"recebido_em": agora - timedelta(hours=3), "mensagem": {"from": 3, "id": 4}},
        {"recebido_em": agora - timedelta(hours=3), "mensagem": {"sender": "!abc", "id": 5}},
        {"recebido_em": agora - timedelta(hours=60), "mensagem": {"from": 1, "id": 6}},  # fora da janela
        {"recebido_em": agora, "mensagem_raw": "lixo"},  # ignorado
    ]
    col.insert_many(docs)
    r = {x["_id"]: x for x in contagem.contar(col, 48)}
    assert r[1]["total"] == 2 and r[1]["diretos"] == 2 and r[1]["por_salto"] == 0
    assert r[2]["por_salto"] == 1 and r[2]["diretos"] == 0
    assert r[3]["sem_info"] == 1
    assert r["!abc"]["total"] == 1
