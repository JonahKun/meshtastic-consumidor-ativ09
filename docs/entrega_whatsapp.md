# Checklist da entrega no grupo do WhatsApp: Atividade 9

Prazo original: 19/10 (entrega atrasada: dizer isso com honestidade na mensagem). Marque cada item só quando o anexo real existir.

| # | Item do enunciado | Anexo / link | Pronto | Quem fez |
|---|---|---|---|---|
| 1 | Foto do gateway instalado (alimentação permanente, local da ativ. 5) | _foto_ | [ ] | _a preencher_ |
| 2 | Print da configuração **sem senha** (papel CLIENT, Wi-Fi 2,4 GHz, MQTT/JSON) | _print_ | [ ] | _a preencher_ |
| 3 | Print do mosquitto_sub/MQTT Explorer com **≥ 3 nós**, um ouvido só por salto | _print_ | [ ] | _a preencher_ |
| 4 | Árvore de tópicos real (ramo JSON) | _print/texto_ | [ ] | _a preencher_ |
| 5 | Link do repositório público do consumidor | _URL_ | [ ] | **Jonah** (consumidor) |
| 6 | Consulta Mongo: contagem por nó nas últimas 48h (com data/hora) | _print/saída_ | [ ] | **Jonah** |
| 7 | Onde e como o consumidor ficou ativo por 48h | _texto + trecho de log_ | [ ] | **Jonah** |
| 8 | Documento de segurança (usuários, permissões, credenciais) | `docs/seguranca.md` | [ ] | **Jonah** (documento); broker/ACL: _a preencher_ |
| 9 | Diário de bordo (problemas e soluções reais) | `docs/diario_de_bordo.md` | [ ] | _a preencher_ |
| 10 | Quem fez cada item | esta tabela | [ ] | _a preencher_ |

## Rascunho da mensagem (preencher os colchetes; não enviar com campos vazios)
```
Atividade 9 - Gateway no ar (entrega em [data/hora], após o prazo de 19/10)

1) Gateway: [local], papel CLIENT, Wi-Fi 2,4 GHz, MQTT com JSON. [foto]
2) Config sem senha: [print]
3) Pacotes no broker: [N] nós ([ids]), sendo [id] ouvido por salto. [print]
4) Árvore de tópicos: [print]
5) Consumidor (paho-mqtt + pymongo) -> coleção pacotes_brutos: [link do repo]
6) Contagem por nó nas últimas 48h: [print / resumo]
   Rodou de [início] a [fim] em [onde], via [docker/systemd]. Interrupções: [ ... ]
7) Segurança: [link/arquivo]
8) Diário de bordo: [link/arquivo]
9) Quem fez o quê: [lista]
```

## Divisão de trabalho (preencher com a real)
| Parte | Responsável |
|---|---|
| Consumidor MQTT -> Mongo, consultas, documentação (configuração, segurança, diário) | Jonah Nishimura Kunihiro |
| Instalação do gateway e foto | _a preencher_ |
| Configuração/ACL do broker | _a preencher_ |
| Prints do broker (3 nós) | _a preencher_ |
| Servidor onde o consumidor roda 48h | _a preencher_ |

Se parte do trabalho não foi feita pelo Jonah (ex.: gateway físico), diga isso explicitamente na mensagem.
