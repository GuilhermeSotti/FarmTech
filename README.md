# 🌾 FarmTech - Orquestrador Consolidado (Fase 7)

Plataforma integrada de IoT, processamento de dados, machine learning e visualização para agricultura de precisão.

## 📋 Estrutura do Projeto

```
farmtech/
├── iot/                     # Firmware e simulação (Arduino/ESP32, Wokwi)
│   ├── sensores/
│   │   ├── esp32_sensor.ino
│   │   └── serial_simulator.py
│   ├── atuadores/
│   │   └── irrigation_control.py
│   └── mqtt_bridge.py
├── data_pipeline/           # Coleta e pré-processamento
│   ├── serial_reader.py
│   ├── config.py
│   └── mqtt_bridge.py
├── ml/                      # Machine Learning
│   ├── train_model.py
│   ├── predict.py
│   ├── train_yolo.py
│   └── utils.py
├── visualization/           # Interface do usuário
│   └── streamlit_app/
│       └── app.py
├── db/                      # Banco de dados
│   ├── schema.sql
│   └── data_samples/
├── aws/                     # Infraestrutura AWS
│   ├── notify.py
│   └── terraform/
├── docker/                  # Containerização
│   ├── Dockerfile
│   └── docker-compose.yml
├── orchestrator.py          # Script mestre
├── requirements.txt
├── .env.template
└── README.md
```

## 🚀 Quick Start

### 1. Clone e Configure

```bash
cd c:\Projetos\FarmTech
cp .env.template .env
# Editar .env com suas credenciais
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Executar Fases

#### Via CLI
```bash
python orchestrator.py --phase iot
python orchestrator.py --phase mqtt
python orchestrator.py --phase streamlit
```

#### Via VS Code Debug
1. Abrir Debug menu (Ctrl+Shift+D)
2. Selecionar configuração desejada
3. Pressionar F5

#### Via Docker
```bash
docker-compose up -d
```

## 📊 Fases do Projeto

| Fase | Descrição | Status |
|------|-----------|--------|
| IoT | Leitura de sensores ESP32/Arduino | ✅ |
| Data Pipeline | Ingestão via Serial/MQTT | ✅ |
| ML | Treinamento e predição | ✅ |
| Vision | Detecção YOLO | ✅ |
| Dashboard | Streamlit integrado | ✅ |
| AWS | Alertas SNS | ✅ |
| Orchestrator | CLI consolidado | ✅ |

## 🔧 Configuração

Edite `.env`:

```env
DATABASE_URL=postgres://user:pass@localhost/farmdb
MQTT_BROKER=broker.hivemq.com
AWS_ACCESS_KEY_ID=xxx
SNS_TOPIC_ARN=arn:aws:sns:...
```

## 📈 Machine Learning

### Treinar Modelo
```bash
python ml/train_model.py --phase training
```

### Fazer Predições
```bash
python ml/predict.py
```

### YOLO Training
```bash
python ml/train_yolo.py
```

## 🗄️ Banco de Dados

### PostgreSQL Local
```bash
docker run -d \
  -e POSTGRES_USER=farmtech \
  -e POSTGRES_PASSWORD=changeme \
  -p 5432:5432 \
  postgres:15
```

### Criar Schema
```bash
psql -U farmtech -d farmdb -f db/schema.sql
```

## 📊 Visualização

Streamlit Dashboard em tempo real:

```bash
streamlit run visualization/streamlit_app/app.py
```

Acesso: http://localhost:8501

## ☁️ AWS SNS

Configurar tópico SNS e credenciais no `.env`:

```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=yyy
python aws/notify.py
```

## 🐳 Docker

Deploy integrado:

```bash
docker-compose up --build
```

Services:
- PostgreSQL: localhost:5432
- Streamlit: localhost:8501

## 📱 Dispositivos Suportados

- **ESP32** com sensor de umidade
- **Arduino** com múltiplos sensores
- **Sensores MQTT** compatíveis
- **Simulador Serial** Python

## 📝 Exemplo de Fluxo Completo

1. **IoT**: Sensor ESP32 publica em MQTT
2. **Pipeline**: MQTT Bridge recebe e salva em CSV
3. **ML**: Modelo treina com dados históricos
4. **Dashboard**: Streamlit exibe em tempo real
5. **Alertas**: SNS notifica via email se crítico

## 🔍 Troubleshooting

### Erro de conexão MQTT
```
Verificar MQTT_BROKER e MQTT_PORT no .env
```

### Erro de banco de dados
```
Verificar DATABASE_URL
docker-compose up db -d (se usar Docker)
```

### Streamlit não carrega
```
streamlit run visualization/streamlit_app/app.py --logger.level=debug
```

## 📚 Documentação Adicional

- [Terraform AWS](aws/terraform/README.md)
- [ML Utils](ml/utils.py)
- [Schema Banco](db/schema.sql)

## 📄 Licença

MIT License - FarmTech 2025

## ✉️ Contato

Suporte: farmtech@example.com
