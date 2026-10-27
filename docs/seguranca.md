# Segurança: broker MQTT, MongoDB e credenciais

Atividade 9 · IAL220 · Fatec Pompeia. **Modelo para preencher com os dados reais.** Um usuário único com permissão total reprova o item; o objetivo é separação por função e mínimo privilégio.

## 1. Usuários do broker e permissões

| Usuário | Quem usa | Pode publicar | Pode assinar | Observações |
|---|---|---|---|---|
| `gw_<id>` | Gateway ESP32 (um por gateway) | `msh/<raiz>/#` | nada | só envia pacotes da malha |
| `consumidor` | Script `consumidor/` (servidor) | nada | `msh/+/2/json/#` | somente leitura |
| `leitura_<nome>` | Alunos/diagnóstico (mosquitto_sub, MQTT Explorer) | nada | `msh/#` | opcional, pode ser temporário |
| `admin` | Professor/responsável do broker | _a preencher_ | _a preencher_ | _não usar no gateway nem no consumidor_ |

Preencha com os nomes reais criados no broker: _a preencher_.

### ACL Mosquitto de exemplo
Arquivo `acl` (referenciado por `acl_file` no `mosquitto.conf`):
```
# gateway: só publica na árvore msh
user gw_EXEMPLO
topic write msh/#

# consumidor: só assina o ramo JSON
user consumidor
topic read msh/+/2/json/#

# leitura de diagnóstico
user leitura_EXEMPLO
topic read msh/#
```
Pontos de atenção:
- Em Mosquitto, `topic write` ao gateway dá só publicação; sem `topic read`, ele não consegue assinar. Se um dia usar *downlink*, abrir apenas o tópico estritamente necessário.
- Senhas com `mosquitto_passwd -c arquivo_senhas usuario` (hash). `allow_anonymous false`.
- `mosquitto.conf` (trecho): `allow_anonymous false`, `password_file ...`, `acl_file ...`, TLS na 8883 se disponível.
- Como o ramo JSON é **sem criptografia**, qualquer assinante com `read msh/#` vê tudo. Por isso a leitura é restrita.

Observação: a configuração do broker pertence ao responsável pelo servidor da disciplina. Se os usuários/ACL foram criados por ele, registre aqui o que foi solicitado e o que foi recebido: _a preencher_.

### MongoDB
| Usuário | Permissão | Escopo |
|---|---|---|
| `consumidor_mongo` | `readWrite` (ou só `insert` + `createIndex` via role customizada) | coleção `pacotes_brutos` do banco `<MONGO_DB>` |
| pipeline (ativ. 10) | leitura em `pacotes_brutos` | mesma coleção |

_a preencher com os usuários reais._

## 2. Onde ficam as credenciais
| Credencial | Onde fica | Quem enxerga |
|---|---|---|
| Wi-Fi + usuário/senha MQTT do gateway | NVS (memória flash) do ESP32, gravada via CLI/app | quem tiver acesso físico/serial ao nó. Anotar quem. |
| Senha MQTT do consumidor e URI do Mongo | arquivo `.env` no servidor onde o consumidor roda (permissão restrita: `chmod 600`; no Docker, `--env-file`) | usuário do servidor que executa o serviço |
| Arquivo de senhas e ACL do broker | servidor do broker | administrador do broker |

Local real do `.env`: _a preencher (máquina/caminho)_.

## 3. O que nunca vai para o repositório
- `.env` (está no `.gitignore`; só o `.env.example` com valores fictícios é versionado)
- Senhas, tokens, URIs com usuário:senha, SSID/PSK do Wi-Fi
- Prints/logs com senhas visíveis (o consumidor mascara a senha da URI do Mongo e nunca loga senhas; ainda assim revise `logs/`)
- Exportações do banco com dados reais, arquivos `*.log`
- Chaves de canal do Meshtastic (PSK) de canais privados

Conferência antes de publicar: pesquisar no repositório por `password`, `psk`, `mongodb://` com senha e IPs/hosts internos. Resultado da conferência: _a preencher_.

## 4. Riscos conhecidos e mitigação
| Risco | Mitigação |
|---|---|
| JSON sem criptografia no broker | ACL de leitura restrita; TLS na conexão com o broker, se disponível |
| Credencial vazada em print | cobrir campos antes de enviar; trocar a senha se vazar |
| Consumidor com permissão excessiva | usuário só-leitura no MQTT; usuário Mongo limitado à coleção |
| Gateway comprometido publicando lixo | publica só em `msh/#`; consumidor grava tudo bruto e o pipeline valida/quarentena |
| Perda do `.env` | guardar cópia segura fora do repositório |

## 5. Rotação
Data da última troca de senhas e responsável: _a preencher_.
