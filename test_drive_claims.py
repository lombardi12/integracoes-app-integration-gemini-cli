import json
import urllib.request
import urllib.error
import google.auth
import google.auth.transport.requests

PROJECT_ID = 'proj-prod-app1-439018'
LOCATION = 'us-central1'
INTEGRATION_NAME = 'drive_claims_to_sheets'
TRIGGER_NAME = 'drive_claims_processor'

creds, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
creds.refresh(google.auth.transport.requests.Request())

headers = {
    'Authorization': f'Bearer {creds.token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

# Example: Testing with a sample claim exceeding R$ 1000
test_payload = {
    "triggerId": f"api_trigger/{TRIGGER_NAME}",
    "inputParameters": {
        "document_name": {
            "stringValue": "Peticao_Inicial_Cobranca_001.pdf"
        },
        "document_content": {
            "stringValue": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL DA COMARCA DA CAPITAL.\n\nAUTOR: Carlos Eduardo Pereira, brasileiro, empresário.\nRÉU: Banco Soluções Financeiras S/A.\nPROCESSO: 1045231-88.2026.8.26.0100\nDATA: 15/11/2026\n\nDOS FATOS E DO PEDIDO:\nO autor ingressa com a presente Ação Declaratória c/c Repetição de Indébito e Indenização por Danos Morais em virtude de descontos indevidos em conta corrente. Requer a condenação da instituição financeira ré ao ressarcimento e pagamento de danos morais.\n\nDO VALOR DA CAUSA:\nDá-se à causa o valor de R$ 12.500,00 (doze mil e quinhentos reais).\nNestes termos, pede deferimento."
        }
    }
}

exec_url = f"https://integrations.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/integrations/{INTEGRATION_NAME}:execute"
req = urllib.request.Request(exec_url, data=json.dumps(test_payload).encode('utf-8'), headers=headers, method='POST')

print(f"Invocando {INTEGRATION_NAME}...")
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Execution ID:", res.get("executionId"))
        print("\nOutput Parameters:")
        print(json.dumps(res.get("outputParameters", {}), indent=2, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
