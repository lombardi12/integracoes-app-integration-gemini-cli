import json
import urllib.request
import subprocess

token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
headers = {'Authorization': f'Bearer {token}'}
url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/executions/3e33d48d-37a2-42ed-967e-e37b3335a2df'
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())

snap4 = data['eventExecutionDetails']['eventExecutionSnapshot'][4]
params_list = snap4['eventParams']['parameters']
param_map = {p['key']: p.get('value', {}) for p in params_list}

body = param_map['`Task_5_responseBody`']['stringValue']
print('Task 5 Body length:', len(body))

# Extraction algorithm in pure JS style
result = None
lines = body.split('\n')
for line in reversed(lines):
    line = line.strip()
    if line.startswith('data:'):
        json_str = line[5:].strip()
        try:
            d = json.loads(json_str)
            if 'artifactUpdate' in d:
                text = d['artifactUpdate']['artifact']['parts'][0]['text']
                if 'acima_de_mil' in text:
                    result = json.loads(text)
                    break
            elif 'statusUpdate' in d:
                text = d['statusUpdate']['status']['message']['content'][0]['text']
                if 'acima_de_mil' in text:
                    result = json.loads(text)
                    break
        except Exception as e:
            pass

print('Extracted result:', json.dumps(result, indent=2, ensure_ascii=False))
