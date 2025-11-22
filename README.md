
# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
  <a href="https://www.fiap.com.br/">
    <img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Administração Paulista" width="40%" />
  </a>
</p>


<br>

# FarmTech

## Nome do grupo: N/A

## 👨‍🎓 Integrantes: 
- Guilherme Pires de Sotti Machado

## 👩‍🏫 Professores:
### Tutor(a) 
- [Guilherme Pires de Sotti Machado](https://www.linkedin.com/in/guilherme-pires-de-sotti-machado-296a7417a/)

### Coordenador(a)
- [Lucas Gomes Moreira](https://www.linkedin.com/in/lucas-gomes-moreira-15a8452a/)

## 📜 Descrição

FarmTech é um orquestrador integrado para agricultura digital que conecta sensores IoT com um pipeline de dados, modelos de machine learning e um painel operacional. O projeto captura leituras de sensores (umidade, nutrientes, temperatura) publicadas via MQTT, ingere e normaliza esses dados, persiste em CSV, processa e treina modelos preditivos (scikit-learn) e apresenta informações e controles em um dashboard em Streamlit. Além disso, o sistema pode emitir alertas por AWS SNS (e-mail/SMS/HTTP) e inclui utilitários para orquestração, logging e testes.

## Video Explicativo
- [VideoExplicativo](https://youtu.be/fjAJs3a27Vk)

## 📁 Estrutura de pastas

- **.github** — workflows de CI/CD e templates do GitHub
- **assets** — imagens e recursos estáticos
- **config** — configurações gerais e templates .env
- **document** — documentação do projeto
- **scripts** — scripts auxiliares (deploy, seed, migrações)
- **src** — código-fonte geral do projeto
- **aws/** — integrações com AWS SNS
- **data/** — módulos para leitura, escrita e ETL
- **db/** — dados CSV e seeds de teste
- **iot/** — sensores, simuladores e mqtt_bridge
- **ml/** — modelos, treinamento e inferência
- **visualization/streamlit_app/** — dashboard Streamlit
- **logs/** — arquivos de log
- **requirements.txt** — dependências Python
- **README.md** — documentação principal

## 🔧 Como executar o código

### Pré-requisitos
- Python 3.10+
- pip
- Virtualenv / venv
- (Opcional) Docker
- (Opcional) AWS CLI configurada
- (Opcional) Broker MQTT (Mosquitto ou HiveMQ)

### Passos principais

1. Criar ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate
# Windows:
# .\.venv\Scriptsctivate
```

2. Instalar dependências:
```bash
pip install -r requirements.txt
```

3. Iniciar mqtt_bridge:
```bash
python iot/mqtt_bridge.py
```

4. Rodar o dashboard:
```bash
streamlit run visualization/streamlit_app/app.py
```

5. Treinar modelo ML:
```bash
python ml/train_model.py
```

6. Enviar alerta SNS:
```bash
python -c "from aws.notify import publish_alert; publish_alert('Teste', 'FarmTech')"
```

## 🗃 Histórico de lançamentos

* 1.0.0 - 2025-11-22  
    * Integração completa das 7 fases  
* 0.9.0 - 2025-11-16  
    * Painel Streamlit consolidado  
* 0.8.0 - 2025-11-12  
    * mqtt_bridge robusto  
* 0.5.0 - 2025-11-07  
    * ML inicial + simuladores  
* 0.1.0 - 2025-10-30  
    * Protótipo básico  

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" 
src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1">
<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" 
src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1">

FarmTech por Grupo FarmTech está licenciado sob Creative Commons — Attribution 4.0 International.
