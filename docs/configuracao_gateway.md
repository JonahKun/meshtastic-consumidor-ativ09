# Configuração do gateway ESP32 (Meshtastic) via CLI

Atividade 9 · IAL220 · Fatec Pompeia · Aluno: Jonah Nishimura Kunihiro · Prof. Allan Siriani

> Este guia usa a documentação oficial do Meshtastic (meshtastic.org/docs: integração MQTT, módulo MQTT e LoRa). Confira a versão do firmware antes de começar: nomes de campos podem mudar entre versões. **Nunca publique senhas** (Wi-Fi, broker) em prints ou no repositório.

## 1. Pré-requisitos
- Placa ESP32 com Meshtastic gravado (o ramo JSON **não existe em nRF52**; só em ESP32).
- Python com a CLI: `pip install --upgrade meshtastic`
- Cabo USB com dados. Porta serial (ex.: `COM5`); se houver mais de um dispositivo, use `--port COM5` em todos os comandos.
- Do professor/servidor: host e porta do broker, usuário e senha **próprios do gateway** e a raiz de tópicos combinada. Preencha em [dados a preencher](#9-dados-a-preencher).

## 2. Papel do nó: CLIENT (e não ROUTER)
```
meshtastic --set device.role CLIENT
```
Justificativa para o relatório:
- `ROUTER` retransmite todos os pacotes que ouve e foi pensado para nós em **pontos altos** e bem posicionados. Roteadores em excesso (ou mal posicionados) aumentam a retransmissão, a ocupação do canal e as colisões, degradando a malha toda.
- O gateway fica em ponto **baixo/interno (indoor)**, perto de roteador Wi-Fi e tomada, ou seja, sem alcance privilegiado. Como `CLIENT`, ele participa da malha, ouve os vizinhos e envia ao broker sem inflar o tráfego.
- O ponto alto de Pompeia (ativ. 7) é que deve receber o papel `ROUTER`, e só ele.
- Observação: o papel `CLIENT_MUTE` também existiria, mas o gateway precisa transmitir (ex.: seu próprio nodeinfo/telemetria), então `CLIENT` é o adequado.

## 3. Região e rádio
```
meshtastic --set lora.region BR_902
```
`BR_902` (Brasil, 902,0 a 907,5 MHz, 30 dBm) é o nome da região no firmware atual conforme a documentação oficial (`meshtastic.org/docs/configuration/radio/lora`). A tabela por país lista também `ANZ` para o Brasil, mas **toda a rede da disciplina deve usar a mesma região e o mesmo preset** (padrão `LONG_FAST`, `hop_limit` 3). Se a lista de regiões do seu firmware não tiver `BR_902`, rode `meshtastic --set lora.region --help` e registre o valor usado no diário. O dispositivo reinicia a cada `--set`; encadear vários `--set` em um comando evita reinícios repetidos.

## 4. Wi-Fi (somente 2,4 GHz)
O ESP32 **não** conecta em 5 GHz. Use o SSID da banda 2,4 GHz (confira o mapa de Wi-Fi da ativ. 5).
```
meshtastic --set network.wifi_enabled true --set network.wifi_ssid "NOME_DA_REDE" --set network.wifi_psk "SENHA_WIFI"
```
(A senha vai só no terminal. Não cole esse comando em prints.)

## 5. Canal e uplink
O módulo só envia ao MQTT os pacotes dos canais com *uplink* ativado:
```
meshtastic --ch-index 0 --ch-set uplink_enabled true
```
`downlink_enabled` fica **desligado** (o gateway só publica, não injeta mensagens na malha). O JSON é enviado sem criptografia, então use apenas o canal da disciplina e evite canais privados com conversas pessoais.

## 6. Módulo MQTT com JSON
```
meshtastic --set mqtt.enabled true --set mqtt.json_enabled true --set mqtt.address HOST_DO_BROKER --set mqtt.username USUARIO_DO_GATEWAY --set mqtt.password SENHA_DO_GATEWAY --set mqtt.root msh/RAIZ --set mqtt.encryption_enabled false --set mqtt.tls_enabled false
```
- `mqtt.address`: se ficar vazio, o nó usa o broker público do Meshtastic. **Preencha sempre** com o broker da disciplina.
- `mqtt.username`/`password`: credencial **própria do gateway** (ver `seguranca.md`); não reutilize a do consumidor nem a de outro aluno.
- `mqtt.root`: raiz dos tópicos. O padrão é `msh/REGIÃO`; use a combinada com a turma (o consumidor assina `msh/+/2/json/#`, que cobre qualquer raiz de dois níveis `msh/<raiz>`). Se a raiz tiver mais de um nível, ajuste `MQTT_TOPIC` no `.env`.
- `mqtt.tls_enabled true` se o broker oferecer TLS (porta 8883); ajuste `MQTT_TLS` no consumidor.
- `mqtt.proxy_to_client_enabled` fica `false` (o nó usa o próprio Wi-Fi).
- `mqtt.map_reporting_enabled`: deixe `false` salvo orientação em contrário.

Conferir (a senha aparece na saída, **cubra-a antes de printar**):
```
meshtastic --get mqtt
meshtastic --get lora
meshtastic --get device
meshtastic --get network
```
Para o print de configuração, prefira a aba de configuração do app Meshtastic ou edite a imagem escondendo `password` e `wifi_psk`.

## 7. Estrutura dos tópicos e do JSON
Conforme a documentação oficial:
- Protobuf (binário): `msh/<raiz>/2/e/<canal>/!<id_gateway>`
- **JSON**: `msh/<raiz>/2/json/<canal>/!<id_gateway>` (ex.: `msh/BR_902/2/json/LongFast/!a1b2c3d4`)

Campos do envelope JSON: `id` (id do pacote), `from` (nó de origem, decimal), `to` (destino, `-1` = broadcast), `sender` (gateway, hex com `!`), `type` (`text`, `nodeinfo`, `position`, `telemetry`, ...), `payload` (objeto, ou string no caso de texto), `timestamp` (epoch **segundos, do nó**: pode estar errado), `channel` (índice do canal). Em versões recentes do firmware aparecem ainda `rssi`, `snr` e `hops_away` (número de saltos; `> 0` indica pacote ouvido por salto). Esses três últimos **não constam na página de MQTT da documentação**; confirme no seu firmware olhando um pacote real e anote em `diario_de_bordo.md`. Se `hops_away` não existir na sua versão, a identificação do nó "ouvido por salto" deve ser feita de outra forma (ex.: nó cujo `from` difere do `sender` e que nunca é ouvido direto, ou pelo app).

A árvore de tópicos que vai na entrega deve ser a **real**, copiada do MQTT Explorer / `mosquitto_sub -v` (não desta seção).

## 8. Checklist de evidências (somente reais)
- [ ] **Foto do gateway** instalado, alimentado, com data/local (descrever onde e como está fixado).
- [ ] **Print da configuração sem senha** (papel CLIENT, região, Wi-Fi 2,4 GHz, MQTT com JSON, endereço do broker). Senhas cobertas.
- [ ] **Print do `mosquitto_sub -v -t 'msh/#' -u <usuario>` ou do MQTT Explorer** mostrando **≥ 3 nós distintos**, sendo **um ouvido só por salto** (`hops_away > 0`), com data/hora visível.
- [ ] **Árvore de tópicos real** (print do MQTT Explorer expandido ou saída de `mosquitto_sub -v` resumida).
- [ ] **Consulta Mongo** com contagem por nó nas últimas 48h (`consultas/contagem_por_no_48h.*`), com data/hora.
- [ ] **Registro das 48h**: onde o consumidor ficou ativo (máquina/servidor), como (docker/systemd/nohup), início e fim, trecho do log com os `HEARTBEAT`.
- [ ] Link do repositório público do consumidor.
- [ ] Links/prints de `seguranca.md` e `diario_de_bordo.md` preenchidos.

Comando de teste (sem expor senha em print: use `-u` e digite a senha só quando solicitada com `-P` fora da tela gravada, ou cubra-a):
```
mosquitto_sub -h HOST_DO_BROKER -p 1883 -u USUARIO -P SENHA -v -t "msh/+/2/json/#"
```

## 9. Dados a preencher
| Item | Valor |
|---|---|
| Broker (host:porta) | _a preencher_ |
| Raiz de tópicos | _a preencher_ |
| ID do gateway (`!xxxxxxxx`) | _a preencher_ |
| Local de instalação | _a preencher_ |
| Versão do firmware | _a preencher_ |
| Placa ESP32 | _a preencher_ |
| Data/hora da instalação | _a preencher_ |
