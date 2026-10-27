"""Contagem de pacotes por no nas ultimas 48h (equivalente em Python de contagem_por_no_48h.js).

Uso:  python consultas/contagem_por_no_48h.py [--horas 48]
Le MONGO_URI, MONGO_DB e MONGO_COLLECTION do .env. Somente leitura.

Colunas: no (mensagem.from; se ausente, mensagem.sender), total, diretos (hops_away == 0),
por_salto (hops_away > 0, ou seja, ouvido por salto), sem_info (sem hops_away), ultimo (recebido_em).
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone


def pipeline(corte: datetime) -> list[dict]:
    hops = "$mensagem.hops_away"
    return [
        {"$match": {"recebido_em": {"$gte": corte}, "mensagem": {"$exists": True}}},
        {"$group": {
            "_id": {"$ifNull": ["$mensagem.from", "$mensagem.sender"]},
            "total": {"$sum": 1},
            "diretos": {"$sum": {"$cond": [{"$eq": [hops, 0]}, 1, 0]}},
            "por_salto": {"$sum": {"$cond": [{"$gt": [hops, 0]}, 1, 0]}},
            "sem_info": {"$sum": {"$cond": [{"$eq": [{"$ifNull": [hops, None]}, None]}, 1, 0]}},
            "ultimo": {"$max": "$recebido_em"},
        }},
        {"$sort": {"total": -1}},
    ]


def contar(colecao, horas: int = 48, agora: datetime | None = None) -> list[dict]:
    agora = agora or datetime.now(timezone.utc)
    return list(colecao.aggregate(pipeline(agora - timedelta(hours=horas))))


def main() -> None:
    from dotenv import load_dotenv
    from pymongo import MongoClient

    ap = argparse.ArgumentParser()
    ap.add_argument("--horas", type=int, default=48)
    args = ap.parse_args()
    load_dotenv()
    cli = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)
    col = cli[os.environ.get("MONGO_DB", "meshtastic")][os.environ.get("MONGO_COLLECTION", "pacotes_brutos")]
    linhas = contar(col, args.horas)
    print(f"Pacotes por no nas ultimas {args.horas}h (consulta em {datetime.now(timezone.utc).isoformat()})")
    print(f"{'no':>12} {'total':>7} {'diretos':>8} {'por_salto':>10} {'sem_info':>9}  ultimo (UTC)")
    for r in linhas:
        print(f"{str(r['_id']):>12} {r['total']:>7} {r['diretos']:>8} {r['por_salto']:>10} "
              f"{r['sem_info']:>9}  {r['ultimo']}")
    print(f"nos distintos: {len(linhas)}  pacotes: {sum(r['total'] for r in linhas)}")


if __name__ == "__main__":
    main()
