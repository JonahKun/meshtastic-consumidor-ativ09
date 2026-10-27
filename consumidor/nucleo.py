"""Logica de tratamento de mensagens, independente de broker (testavel sem rede).

Contrato gravado em `pacotes_brutos`:
    {topico: str, recebido_em: datetime UTC, mensagem: <JSON original, inalterado>}
    ou, se o payload nao for JSON valido:
    {topico: str, recebido_em: datetime UTC, mensagem_raw: <texto>}
Nenhuma mensagem e descartada.
"""
from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

log = logging.getLogger("consumidor")


def montar_documento(topico: str, payload: bytes | str, recebido_em: datetime | None = None) -> dict:
    """Constroi o documento sem transformar o conteudo da mensagem."""
    recebido_em = recebido_em or datetime.now(timezone.utc)
    if isinstance(payload, (bytes, bytearray)):
        texto = bytes(payload).decode("utf-8", errors="replace")
    else:
        texto = payload
    try:
        mensagem = json.loads(texto)
    except (ValueError, RecursionError):
        return {"topico": topico, "recebido_em": recebido_em, "mensagem_raw": texto}
    return {"topico": topico, "recebido_em": recebido_em, "mensagem": mensagem}


class Armazenamento:
    """Grava no Mongo; se cair, guarda em buffer limitado e reenvia depois."""

    def __init__(self, colecao, buffer_max: int = 10000):
        self.colecao = colecao
        self.buffer: deque[dict] = deque()
        self.buffer_max = buffer_max
        self.lock = threading.Lock()
        self.recebidas = 0
        self.gravadas = 0
        self.falhas = 0          # tentativas de gravacao que falharam (mensagem foi para o buffer)
        self.descartadas = 0     # so ocorre se o buffer estourar durante queda longa do Mongo
        self.json_invalido = 0
        self.indices_ok = False

    # -- indices --------------------------------------------------------
    def criar_indices(self) -> bool:
        try:
            self.colecao.create_index("recebido_em", name="idx_recebido_em")
            self.colecao.create_index([("mensagem.from", 1), ("mensagem.id", 1)], name="idx_from_id")
            self.indices_ok = True
            log.info("Indices garantidos (recebido_em; mensagem.from+mensagem.id, nao unico)")
        except PyMongoError as e:
            self.indices_ok = False
            log.warning("Nao foi possivel criar indices agora (%s); tentarei de novo", type(e).__name__)
        return self.indices_ok

    # -- gravacao -------------------------------------------------------
    def tratar_mensagem(self, topico: str, payload: bytes | str) -> dict:
        doc = montar_documento(topico, payload)
        with self.lock:
            self.recebidas += 1
            if "mensagem_raw" in doc:
                self.json_invalido += 1
            self._gravar(doc)
        return doc

    def _gravar(self, doc: dict) -> None:
        # reenvia primeiro o que ficou pendente, para manter a ordem
        if self.buffer and not self._esvaziar_buffer():
            self._empilhar(doc)
            return
        try:
            self.colecao.insert_one(dict(doc))
            self.gravadas += 1
        except PyMongoError as e:
            self.falhas += 1
            log.warning("Falha ao gravar no Mongo (%s); mensagem em buffer", type(e).__name__)
            self._empilhar(doc)
        except (OverflowError, ValueError, TypeError) as e:
            # JSON valido que o BSON nao representa (ex.: inteiro > 64 bits): nao descartar,
            # guardar o texto original.
            self.falhas += 1
            log.warning("BSON recusou o documento (%s); gravando como mensagem_raw", type(e).__name__)
            bruto = {"topico": doc["topico"], "recebido_em": doc["recebido_em"],
                     "mensagem_raw": json.dumps(doc.get("mensagem"), ensure_ascii=False)}
            try:
                self.colecao.insert_one(bruto)
                self.gravadas += 1
                self.json_invalido += 1
            except PyMongoError:
                self._empilhar(bruto)

    def _empilhar(self, doc: dict) -> None:
        if len(self.buffer) >= self.buffer_max:
            self.buffer.popleft()
            self.descartadas += 1
            log.error("Buffer cheio (%d); descartando a mensagem mais antiga", self.buffer_max)
        self.buffer.append(doc)

    def _esvaziar_buffer(self) -> bool:
        """Tenta gravar o buffer em lotes. Retorna True se esvaziou."""
        while self.buffer:
            lote = [self.buffer[i] for i in range(min(500, len(self.buffer)))]
            try:
                self.colecao.insert_many([dict(d) for d in lote], ordered=True)
            except PyMongoError:
                return False
            for _ in lote:
                self.buffer.popleft()
            self.gravadas += len(lote)
        log.info("Buffer reenviado ao Mongo com sucesso")
        return True

    def manutencao(self) -> None:
        """Chamado periodicamente: recria indices e reenvia buffer pendente."""
        with self.lock:
            if not self.indices_ok:
                self.criar_indices()
            if self.buffer:
                self._esvaziar_buffer()

    def estatisticas(self) -> str:
        with self.lock:
            return (f"recebidas={self.recebidas} gravadas={self.gravadas} falhas={self.falhas} "
                    f"json_invalido={self.json_invalido} no_buffer={len(self.buffer)} "
                    f"descartadas={self.descartadas}")
