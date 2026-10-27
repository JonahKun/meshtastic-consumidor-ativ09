# Diário de bordo: Atividade 9 (Gateway no ar)

**MODELO VAZIO.** Registre somente o que de fato aconteceu, com data e hora reais. Não invente entradas: o diário vale como evidência e honestidade conta na avaliação (ver P1).

| Data/hora | Problema | Causa | Solução | Quem |
|---|---|---|---|---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

## Categorias de exemplo (para lembrar o que anotar; não são entradas)
- **Queda de Wi-Fi**: nó some do broker; conferir 2,4 GHz, sinal, reinício do roteador, reconexão do ESP32.
- **Broker recusou a conexão**: usuário/senha, ACL, porta, TLS, client_id duplicado (dois consumidores com o mesmo client_id se derrubam).
- **JSON vazio ou inválido**: `json_enabled` desligado, canal sem uplink, pacote truncado. O consumidor guarda como `mensagem_raw`.
- **Nó sumiu**: bateria, fora de alcance, sem salto disponível, relógio errado.
- **Mongo indisponível**: o consumidor guarda em buffer; anotar quanto tempo e se houve descarte (`descartadas` no heartbeat).
- **Consumidor parou**: processo morto, reinício do servidor, política de restart.
- **Timestamps errados**: nó sem hora (epoch 0 ou futuro); a referência é `recebido_em`.
- **Duplicatas**: mesmo `from`+`id` ouvido por gateways diferentes (esperado; tratado no pipeline).

## Registro das 48h
| Item | Valor |
|---|---|
| Início da execução (data/hora) |  |
| Fim (data/hora) |  |
| Onde rodou (máquina/servidor) |  |
| Como ficou ativo (docker/systemd/nohup) |  |
| Interrupções |  |
| Total de mensagens gravadas (último HEARTBEAT) |  |
