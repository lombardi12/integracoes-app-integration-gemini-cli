# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib.request
import subprocess

PROJECT_ID = 'proj-prod-app1-439018'
LOCATION = 'us-central1'
INTEGRATION_NAME = 'drive_claims_to_sheets'
TRIGGER_NAME = 'drive_claims_processor'

token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

petition_text = """PETIÇÃO INICIAL
Autos do Processo nº 1045892-71.2024.8.26.0100
EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA 2ª VARA CÍVEL DA COMARCA DE SÃO PAULO - SP

I. QUALIFICAÇÃO DAS PARTES
CARLOS EDUARDO MOREIRA, brasileiro, solteiro, analista de sistemas, RG nº 28.451.992-X SSP/SP, CPF nº 123.456.789-00, residente na Rua das Flores, 140, São Paulo/SP, por seu advogado, vem propor a presente:
AÇÃO DE COBRANÇA C/C INDENIZAÇÃO POR PERDAS E DANOS
em face de VAREJO TECH COMÉRCIO E SERVIÇOS DIGITAIS LTDA., CNPJ nº 44.555.666/0001-88, com sede na Av. Paulista, 1000, 5º andar, São Paulo/SP, pelos fatos a seguir expostos.

II. DOS FATOS E DO INADIMPLEMENTO
O Autor firmou com a Ré Contrato de Serviços de Nuvem em 15/05/2024. Todos os serviços foram homologados em 20/10/2024.
Resta pendente a parcela de R$ 3.250,00, vencida em 01/11/2024. As despesas operacionais adicionais decorrentes do inadimplemento somam R$ 1.500,00.

III. DOS PEDIDOS E REQUERIMENTOS
Diante do exposto, requer a Vossa Excelência:
A citação da Ré para responder à presente ação sob pena de revelia;
A procedência para condenar a Ré ao pagamento principal de R$ 3.250,00;
A condenação da Ré a indenização por perdas e danos de R$ 1.500,00;
A condenação da Ré em custas processuais e honorários advocatícios.

IV. DO VALOR DA CAUSA
Dá-se à causa o valor de R$ 4.750,00 (quatro mil e setecentos e cinquenta reais).

V. ENCERRAMENTO E DATA
Termos em que, pede e espera deferimento.
São Paulo/SP, 14 de novembro de 2024.
Carlos Eduardo Moreira - OAB/SP 499.123"""

test_payload = {
    "triggerId": f"api_trigger/{TRIGGER_NAME}",
    "inputParameters": {
        "document_name": {
            "stringValue": "Peticao_Inicial_Carlos_Eduardo_Moreira.gdoc"
        },
        "document_content": {
            "stringValue": petition_text
        }
    }
}

exec_url = f"https://integrations.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/integrations/{INTEGRATION_NAME}:execute"
req = urllib.request.Request(exec_url, data=json.dumps(test_payload).encode('utf-8'), headers=headers, method='POST')

print(f"Executando {INTEGRATION_NAME}...")
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print("Execution ID:", res.get("executionId"))
    print("\nOutput Parameters:")
    print(json.dumps(res.get("outputParameters", {}), indent=2, ensure_ascii=False))
