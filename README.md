# 🌐 Google Cloud Application Integration Agent Lab (`appint-agent-lab`)

[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Application_Integration-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/application-integration)
[![Vertex AI](https://img.shields.io/badge/Vertex_AI-Gemini-8E75B2?logo=google&logoColor=white)](https://cloud.google.com/vertex-ai)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Este repositório contém um laboratório de referência para construção, teste, publicação e orquestração de fluxos corporativos no **Google Cloud Application Integration**, utilizando **Vertex AI (Gemini)**, **Google Drive**, **Google Sheets**, **BigQuery** e **Salesforce CDC**, além de **Skills de Agentes de IA** (`agent skills`) para desenvolvimento assistido por modelos de linguagem (Gemini CLI, Claude Code, etc.).

---

## 📋 Sumário

- [Visão Geral da Arquitetura](#-visão-geral-da-arquitetura)
- [Integrações Implementadas](#-integrações-implementadas)
  - [1. Processamento Inteligente de Documentos com Vertex AI (`drive_claims_to_sheets`)](#1-pipeline-inteligente-de-sinistros-e-documentos-drive_claims_to_sheets)
  - [2. Ingestão de Salesforce CDC para BigQuery (`salesforce_opportunity_to_bigquery`)](#2-ingestão-de-salesforce-cdc-para-bigquery-salesforce_opportunity_to_bigquery)
  - [3. Motor de Adjudicação de Sinistros (`sample-claims-adjudication.json`)](#3-motor-de-adjudicação-de-sinistros-sample-claims-adjudicationjson)
- [Skills de Agentes de IA (`.agents/skills/`)](#-skills-de-agentes-de-ia-agentsskills)
- [Estrutura do Repositório](#-estrutura-do-repositório)
- [Pré-requisitos e Configuração no Google Cloud](#-pré-requisitos-e-configuração-no-google-cloud)
- [Guia Passo a Passo de Implantação (Deploy)](#-guia-passo-a-passo-de-implantação-deploy)
- [Como Executar e Testar (Exemplos Práticos)](#-como-executar-e-testar-exemplos-práticos)
- [Boas Práticas e Troubleshooting](#-boas-práticas-e-troubleshooting)

---

## 🏗 Visão Geral da Arquitetura

O Application Integration atua como o barramento corporativo serverless no GCP, orquestrando eventos e APIs com suporte a autenticação nativa, transformações JavaScript em engine V8 e conectores corporativos.

```
                              ┌──────────────────────────────────────────────┐
                              │          Google Cloud Project                │
                              │                                              │
  ┌──────────────────┐        │  ┌────────────────────────────────────────┐  │        ┌──────────────────┐
  │   Google Drive   │◄───────┼──┤  Task 1: List Files (Drive API)        │  │        │   Google Docs    │
  │  (Pasta Monitor) │        │  └──────────────────┬─────────────────────┘  │        │  (Export Texto)  │
  └──────────────────┘        │                     ▼                        │        └──────────────────┘
                              │  ┌────────────────────────────────────────┐  │                 ▲
  ┌──────────────────┐        │  │  Task 2: Select File or Direct Input   │──┼─────────────────┘
  │   API Trigger    ├───────►│  └──────────────────┬─────────────────────┘  │
  │ (Payload Manual) │        │                     ▼                        │        ┌──────────────────┐
  └──────────────────┘        │  ┌────────────────────────────────────────┐  │        │    Vertex AI     │
                              │  │  Task 4 & 5: Vertex AI Agent / Gemini  │◄─┼───────►│  (Gemini Model / │
                              │  └──────────────────┬─────────────────────┘  │        │   Agent Garden)  │
                              │                     ▼                        │        └──────────────────┘
                              │  ┌────────────────────────────────────────┐  │
                              │  │  Task 6: Parsing & Avaliação Regra     │  │
                              │  │          (Valor > R$ 1.000,00)         │  │
                              │  └──────────────────┬─────────────────────┘  │        ┌──────────────────┐
                              │                     ▼                        │        │  Google Sheets   │
                              │  ┌────────────────────────────────────────┐  │───────►│ (Painel/Planilha │
                              │  │  Task 7: Append Row (Sheets API)       │  │        │   Consolidada)   │
                              │  └────────────────────────────────────────┘  │        └──────────────────┘
                              └──────────────────────────────────────────────┘
```

---

## 🚀 Integrações Implementadas

### 1. Pipeline Inteligente de Sinistros e Documentos (`drive_claims_to_sheets`)

- **Arquivo JSON de Definição:** `drive_claims_integration.json`
- **Triggers:**
  - `api_trigger/drive_claims_processor`: Disparo síncrono via API com dados de petição/documento em texto direto ou indicando arquivo no Drive.
  - `cron_trigger/drive_claims_schedule`: Varredura periódica da pasta no Google Drive a cada 15 minutos.
- **Fluxo de Execução:**
  1. **Task 1 (`GenericRestV2Task`):** Consulta a pasta de entrada do Drive via endpoint `https://www.googleapis.com/drive/v3/files?q='FOLDER_ID'+in+parents+and+mimeType!='application/vnd.google-apps.folder'+and+trashed=false`.
  2. **Task 2 (`JavaScriptTask`):** Avalia se foi passado um documento direto no payload ou se existe arquivo na pasta. Caso seja um Google Docs, configura rota para exportação em texto plano; se for binário/PDF, rota para download de mídia.
  3. **Task 3 (`GenericRestV2Task`):** Efetua o download/exportação do conteúdo do documento.
  4. **Task 4 (`JavaScriptTask`):** Sanitiza o texto, remove quebras excessivas e monta a mensagem no padrão esperado pelo agente de raciocínio.
  5. **Task 5 (`GenericRestV2Task`):** Invoca o modelo/agente na Vertex AI (ex: Gemini em `us-west1` ou `us-central1`), extraindo entidades críticas:
     - `autor` (Requerente)
     - `reu` (Instituição / Empresa Ré)
     - `numero_processo`
     - `data_fato`
     - `valor_da_causa`
     - `acima_de_mil` (Booleano)
  6. **Task 6 (`JavaScriptTask`):** Extrai o JSON retornado pela IA e formata a linha de dados para a planilha.
  7. **Task 7 (`GenericRestV2Task`):** Realiza `POST` no Google Sheets API (`values/{range}:append?valueInputOption=USER_ENTERED`) registrando o sinistro/petição aprovado.
  8. **Task 8 (`JavaScriptTask`):** Monta payload de saída do fluxo (`processed_claims_summary`).
  9. **Task 9 (`GenericRestV2Task`):** Move o arquivo processado para a subpasta de arquivamento no Google Drive.

---

### 2. Ingestão de Salesforce CDC para BigQuery (`salesforce_opportunity_to_bigquery`)

- **Scripts:** `deploy_and_test.py` e `execute_test.py`
- **Objetivo:** Captura de eventos Change Data Capture (CDC) de Oportunidades do Salesforce e ingestão direta no BigQuery via streaming insert.
- **Fluxo de Execução:**
  1. **Trigger:** `api_trigger/salesforce_opportunity_test` recebe o evento CDC do Salesforce.
  2. **Task 1 (`JavaScriptTask`):** Normaliza o JSON do evento (ID, Nome, Valor, Estágio, Data de Fechamento, Tipo de Mudança e Timestamp de ingestão) gerando a estrutura `bigquery#tableDataInsertAllRequest`.
  3. **Task 2 (`GenericRestV2Task`):** Invoca a API de streaming do BigQuery (`insertAll`) gravando diretamente na tabela de staging.

---

### 3. Motor de Adjudicação de Sinistros (`sample-claims-adjudication.json`)

- **Objetivo:** Demonstração de regras de decisão nativas no Application Integration.
- **Entradas:** `claimId`, `claimAmount`, `policyActive`.
- **Decisões:**
  - `APPROVED`: Se apólice ativa e valor <= R$ 1.000,00.
  - `MANUAL_REVIEW`: Se apólice ativa e valor > R$ 1.000,00.
  - `DENIED`: Se apólice inativa.

---

## 🤖 Skills de Agentes de IA (`.agents/skills/`)

Este repositório inclui três Agent Skills que seguem o padrão aberto de extensão de agentes LLM (como Gemini CLI, Claude Code e Google Cloud Assist):

| Skill | Localização | Descrição |
| :--- | :--- | :--- |
| **`application-integration-authoring`** | `.agents/skills/application-integration-authoring` | Criação declarativa, versionamento, upload de JSON, publicação de rascunhos, configuração de parâmetros e execução via REST API. |
| **`application-integration-basics`** | `.agents/skills/application-integration-basics` | Provisionamento de regiões no Application Integration, arquitetura, limites da plataforma, papéis de IAM e Service Accounts (`runAsServiceAccount`). |
| **`application-integration-troubleshooting`** | `.agents/skills/application-integration-troubleshooting` | Diagnóstico de falhas, consulta a execuções suspensas, filtros no Cloud Logging, auditoria de connectors e recuperação de integridade. |

Cada skill contém um `SKILL.md` detalhado e guias em `references/` cobrindo padrões, gotchas e comandos da API REST.

---

## 📂 Estrutura do Repositório

```
appint-agent-lab/
├── README.md                              # Documentação completa do projeto
├── .env.example                           # Exemplo de variáveis de ambiente do laboratório
├── .gitignore                             # Regras de exclusão de arquivos no Git
├── drive_claims_integration.json          # Definição completa do fluxo Drive -> Vertex AI -> Sheets
├── sample-claims-adjudication.json        # Template de adjudicação automática de sinistros
│
├── deploy_drive_claims.py                 # Script de upload e publicação da integração de sinistros
├── build_and_deploy_final_integration.py  # Script de consolidação de AuthConfig e deploy
├── deploy_and_test_docs_export.py         # Atualiza lógica de exportação de Docs e publica
├── deploy_and_test.py                     # Deploy do pipeline Salesforce CDC para BigQuery
├── finalize_integration.py                # Ajusta filtros de pastas do Drive e rotas
├── update_drive_claims_logic.py           # Atualizações pontuais do script JavaScript V8
│
├── execute_test.py                        # Execução de teste do fluxo Salesforce -> BigQuery
├── test_drive_claims.py                   # Invocação de teste da integração de documentos via API
├── test_carlos_eduardo_petition.py        # Teste com petição jurídica real (valor > R$ 1.000)
├── test_connector_task.py                 # Validação de Integration Connectors vs REST API
├── test_sheets_connector.py               # Teste específico de conexão com Google Sheets Connector
├── test_auth_profile_rest.py              # Teste de AuthConfig em GenericRestV2Task
├── test_native_sheets.py                  # Teste de task nativa do Sheets
├── debug_extract.py                       # Utilitário para depurar snapshots de execução e respostas da IA
│
└── .agents/                               # Skills de IA para Application Integration
    └── skills/
        ├── application-integration-authoring/
        ├── application-integration-basics/
        └── application-integration-troubleshooting/
```

---

## ⚙️ Pré-requisitos e Configuração no Google Cloud

### 1. Ferramentas Necessárias

- **Google Cloud SDK (`gcloud`)** instalado e autenticado:
  ```bash
  gcloud auth login
  gcloud config set project SEU_PROJECT_ID
  ```
- **Python 3.10+** com bibliotecas de autenticação do Google:
  ```bash
  pip install google-auth requests google-cloud-bigquery
  ```

### 2. Ativar as APIs no Google Cloud

```bash
gcloud services enable \
  integrations.googleapis.com \
  connectors.googleapis.com \
  aiplatform.googleapis.com \
  drive.googleapis.com \
  sheets.googleapis.com \
  bigquery.googleapis.com \
  iamcredentials.googleapis.com
```

### 3. Service Account e Papéis de IAM

Crie a Service Account que executará os fluxos (`runAsServiceAccount`):

```bash
gcloud iam service-accounts create appint-drive-sheets \
  --display-name="App Integration Service Account"

SA_EMAIL="appint-drive-sheets@$(gcloud config get-value project).iam.gserviceaccount.com"

# Atribuição de permissões
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/integrations.integrationAdmin"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor"
```

> **Atenção:** Para acessar Google Drive e Google Sheets, compartilhe a pasta do Drive e a Planilha diretamente com o e-mail da Service Account (`appint-drive-sheets@...`) como **Editor**.

### 4. Auth Profile (AuthConfig)

No Application Integration, crie um **Auth Profile** do tipo **Service Account Auth** associado à Service Account criada. Esse Auth Profile fornecerá os tokens Bearer automaticamente para as tarefas `GenericRestV2Task` ao chamar APIs do Google (`drive.googleapis.com`, `sheets.googleapis.com`).

---

## 📦 Guia Passo a Passo de Implantação (Deploy)

### Passo 1: Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e preencha com seus dados:

```bash
cp .env.example .env
```

Atualize no arquivo `drive_claims_integration.json` (ou use os scripts de deploy):
- O ID do AuthConfig (`auth_config_id`)
- O e-mail da Service Account (`runAsServiceAccount`)
- O ID da pasta do Drive na Task 1
- O ID da Planilha do Google Sheets na Task 7

### Passo 2: Implantar a Integração `drive_claims_to_sheets`

Execute o script de build e publicação:

```bash
python3 build_and_deploy_final_integration.py
```

Esse script irá:
1. Validar e injetar o `authConfig` nas tarefas REST de Drive e Sheets.
2. Atualizar o `runAsServiceAccount`.
3. Fazer o upload do rascunho (`versions:upload`) no Application Integration.
4. Publicar automaticamente a versão para torná-la `ACTIVE`.

### Passo 3: Implantar a Integração Salesforce CDC para BigQuery

```bash
python3 deploy_and_test.py
```

---

## 🧪 Como Executar e Testar (Exemplos Práticos)

### Exemplo 1: Testar Processamento de Documento via Script Python

Execute o teste de envio de uma Petição Inicial completa:

```bash
python3 test_carlos_eduardo_petition.py
```

**Resultado esperado:**
- A integração recebe o texto da petição.
- O agente na Vertex AI analisa os pedidos e identifica o valor da causa (`R$ 4.750,00`).
- Como `4750 > 1000`, a condição de aprovação é atendida.
- Uma nova linha é inserida na planilha do Google Sheets com:
  `Data | Documento | Autor | Réu | Processo | Valor | Status`.

### Exemplo 2: Invocação Direta via `curl` (API REST)

```bash
PROJECT_ID="proj-prod-app1-439018"
LOCATION="us-central1"
INTEGRATION="drive_claims_to_sheets"

curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "triggerId": "api_trigger/drive_claims_processor",
    "inputParameters": {
      "document_name": {
        "stringValue": "Peticao_Acordo_Trabalhista.pdf"
      },
      "document_content": {
        "stringValue": "AÇÃO INDENIZATÓRIA. Autor: Carlos Silva. Réu: Empresa XPTO. Valor da Causa: R$ 8.500,00. Requer condenação."
      }
    }
  }' \
  "https://integrations.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/integrations/${INTEGRATION}:execute"
```

### Exemplo 3: Testar Fluxo de CDC Salesforce para BigQuery

```bash
python3 execute_test.py
```

---

## 💡 Boas Práticas e Troubleshooting

1. **Engine JavaScript (V8):**
   - Ao criar `JavaScriptTask` no Application Integration, declare **ambas** as funções `executeScript(event)` e `executesScript(event)`:
     ```javascript
     function executeScript(event) {
       return executesScript(event);
     }
     var executesScript = executeScript;
     ```
   - Isso evita erros de runtime causados por variações de nomenclatura interna da plataforma.

2. **Google Docs vs PDFs no Drive:**
   - Arquivos nativos do Google Docs (`application/vnd.google-apps.document`) **não** podem ser baixados com `alt=media`. Utilize a rota de exportação:
     `https://www.googleapis.com/drive/v3/files/{fileId}/export?mimeType=text/plain`

3. **Status HTTP 200 não garante sucesso de todas as Tasks:**
   - O endpoint `:execute` pode responder HTTP 200 mesmo se uma task interna falhar com `throwError: false`.
   - Utilize o utilitário `debug_extract.py` ou consulte a API de execuções para inspecionar os detalhes:
     ```bash
     curl -sS -H "Authorization: Bearer $(gcloud auth print-access-token)" \
       "https://integrations.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/integrations/${INTEGRATION}/executions/${EXECUTION_ID}"
     ```

---

## 📄 Licença & Aviso Legal (Disclaimer)

Distribuído sob a licença **Apache License 2.0**. Consulte o arquivo [LICENSE](LICENSE) para obter o texto completo da licença.

> **Aviso (AS-IS Notice):** Este repositório contém código de exemplo e demonstração publicado "NO ESTADO EM QUE SE ENCONTRA" (AS-IS), sem garantias ou condições de qualquer tipo. Este não é um produto oficial com suporte do Google.
