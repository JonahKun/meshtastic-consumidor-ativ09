"""SIMULADOR DE PACOTES MESHTASTIC JSON  --  SOMENTE PARA TESTE LOCAL.

##########################################################################
#  ATENCAO: ESTES DADOS SAO FALSOS. Nao use prints, contagens ou          #
#  documentos gerados por este script como evidencia de entrega da        #
#  Atividade 9. Evidencia forjada zera a nota (ver P1). Use apenas para   #
#  testar o consumidor num broker/Mongo LOCAIS (ex.: mosquitto local).    #
##########################################################################

Para nao alterar o formato dos pacotes, o marcador de "falso" fica no topico: a raiz usada e
"msh/SIMULADO/2/json/...". Os ids de no sao inventados.

Uso:
    python ferramentas/simulador.py --host localhost --port 1883 --rodadas 3
Recusa-se a rodar contra um host que nao seja local, a menos que --eu-sei-que-e-teste seja passado.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time

import paho.mqtt.client as mqtt

LOCAIS = {"localhost", "127.0.0.1", "::1"}
RAIZ = "msh/SIMULADO"
NOS = {111111111: "!069f6bc7", 222222222: "!0d3a1c8e", 333333333: "!13d4fa71"}  # ids inventados
GATEWAYS = ["!aaaa0001", "!bbbb0002"]
_id = random.randint(1_000_000, 9_000_000)


def _novo_id() -> int:
    global _id
    _id += 1
    return _id


def _env(de, tipo, payload, gw, hops, ts=None, id_=None):
    return {
        "channel": 0, "from": de, "hops_away": hops, "id": id_ or _novo_id(),
        "payload": payload, "rssi": random.randint(-120, -60), "sender": gw,
        "snr": round(random.uniform(-15, 10), 2),
        "timestamp": ts if ts is not None else int(time.time()), "to": -1, "type": tipo,
    }


def gerar_rodada() -> list[tuple[str, str]]:
    """Retorna lista de (topico, payload_texto)."""
    msgs: list[tuple[str, str]] = []
    gw = GATEWAYS[0]

    def topico(g):
        return f"{RAIZ}/2/json/LongFast/{g}"

    nos = list(NOS)
    for i, no in enumerate(nos):
        hops = 0 if i == 0 else i  # no 1 direto; nos 2 e 3 ouvidos por salto
        msgs.append((topico(gw), json.dumps(_env(no, "telemetry", {
            "battery_level": random.randint(20, 100), "voltage": round(random.uniform(3.4, 4.2), 2),
            "channel_utilization": round(random.uniform(0, 25), 2),
            "air_util_tx": round(random.uniform(0, 3), 2), "uptime_seconds": random.randint(100, 900000)},
            gw, hops))))
        msgs.append((topico(gw), json.dumps(_env(no, "telemetry", {
            "temperature": round(random.uniform(15, 35), 1),
            "relative_humidity": round(random.uniform(30, 90), 1),
            "barometric_pressure": round(random.uniform(1000, 1020), 1)}, gw, hops))))
    msgs.append((topico(gw), json.dumps(_env(nos[0], "position", {
        "latitude_i": -224500000, "longitude_i": -499500000, "altitude": 480, "time": int(time.time())}, gw, 0))))
    msgs.append((topico(gw), json.dumps(_env(nos[1], "nodeinfo", {
        "id": NOS[nos[1]], "longname": "No Simulado 2", "shortname": "NS2", "hardware": 43, "role": 1}, gw, 1))))
    msgs.append((topico(gw), json.dumps(_env(nos[2], "text", "ola, mensagem de teste", gw, 2))))

    # duplicata: mesmo from+id ouvido por dois gateways diferentes
    dup = _env(nos[1], "telemetry", {"battery_level": 77, "voltage": 3.95}, gw, 1)
    msgs.append((topico(GATEWAYS[0]), json.dumps(dup)))
    dup2 = dict(dup, sender=GATEWAYS[1], rssi=-101, snr=-3.0)
    msgs.append((topico(GATEWAYS[1]), json.dumps(dup2)))

    # timestamps errados: epoch 0, passado distante e futuro
    for ts in (0, 946684800, int(time.time()) + 10 * 365 * 86400):
        msgs.append((topico(gw), json.dumps(_env(nos[0], "telemetry", {"battery_level": 50, "voltage": 3.8}, gw, 0, ts=ts))))

    # JSON invalido e payload vazio
    msgs.append((topico(gw), '{"from": 111111111, "id": 99, "payload": '))
    msgs.append((topico(gw), ""))
    return msgs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--user")
    ap.add_argument("--password")
    ap.add_argument("--rodadas", type=int, default=1)
    ap.add_argument("--intervalo", type=float, default=1.0)
    ap.add_argument("--eu-sei-que-e-teste", action="store_true", help="permite host nao local")
    a = ap.parse_args()

    if a.host not in LOCAIS and not a.eu_sei_que_e_teste:
        print("Recusado: host nao e local. Este simulador gera dados FALSOS e nao deve poluir o broker da disciplina.")
        return 2
    print("AVISO: publicando dados FALSOS (teste local). NAO usar como evidencia de entrega.")

    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="simulador-teste-local")
    if a.user:
        cli.username_pw_set(a.user, a.password)
    cli.connect(a.host, a.port, 60)
    cli.loop_start()
    total = 0
    for r in range(a.rodadas):
        for top, payload in gerar_rodada():
            cli.publish(top, payload, qos=1).wait_for_publish(5)
            total += 1
        print(f"rodada {r + 1}/{a.rodadas} publicada")
        time.sleep(a.intervalo)
    cli.loop_stop()
    cli.disconnect()
    print(f"{total} mensagens publicadas (todas SIMULADAS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
