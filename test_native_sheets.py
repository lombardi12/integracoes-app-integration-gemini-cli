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

import urllib.request
import json
import subprocess

token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

test_int = {
    'description': 'Test native Sheets - Append task',
    'runAsServiceAccount': 'appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com',
    'triggerConfigs': [
        {
            'label': 'Test Trigger Sheets Append',
            'triggerType': 'API',
            'triggerNumber': '1',
            'triggerId': 'api_trigger/test_sheets_append',
            'properties': {'Trigger name': 'test_sheets_append'},
            'startTasks': [{'taskId': '1'}]
        }
    ],
    'taskConfigs': [
        {
            'task': 'Sheets - Append',
            'taskId': '1',
            'displayName': 'Append Claim to Google Sheets',
            'parameters': {
                'authConfig': {
                    'key': 'authConfig',
                    'value': {
                        'stringValue': 'projects/1023905883743/locations/us-central1/authConfigs/e2bbf6a3-8d6b-43a4-a491-5011bc9bee1e'
                    }
                },
                'spreadsheetId': {
                    'key': 'spreadsheetId',
                    'value': {
                        'stringValue': '1mjqIz1LvNwyZSj1_LTfKcMVbb4jDIULjNb-YQmkrKr8'
                    }
                },
                'range': {
                    'key': 'range',
                    'value': {
                        'stringValue': 'Sheet1!A1'
                    }
                },
                'valueInputOption': {
                    'key': 'valueInputOption',
                    'value': {
                        'stringValue': 'USER_ENTERED'
                    }
                },
                'values': {
                    'key': 'values',
                    'value': {
                        'jsonValue': json.dumps([
                            ["20/11/2026 01:25", "Peticao_Inicial_Cobranca_001.pdf", "Petição Inicial", "1045231-88.2026.8.26.0100", "Carlos Eduardo Pereira", "Banco Soluções Financeiras S/A", 12500, "Resumo via Sheets - Append nativo"]
                        ])
                    }
                }
            }
        }
    ]
}

url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions:upload'
req = urllib.request.Request(url, data=json.dumps({'content': json.dumps(test_int), 'fileFormat': 'JSON'}).encode(), headers=headers, method='POST')
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    vid = res['integrationVersion']['name'].split('/')[-1]
    print('Uploaded draft:', vid)

pub_url = f'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions/{vid}:publish'
pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
with urllib.request.urlopen(pub_req) as pub_resp:
    print('Published status:', pub_resp.status)

exec_url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets:execute'
exec_payload = {'triggerId': 'api_trigger/test_sheets_append'}
exec_req = urllib.request.Request(exec_url, data=json.dumps(exec_payload).encode('utf-8'), headers=headers, method='POST')
try:
    with urllib.request.urlopen(exec_req) as exec_resp:
        exec_res = json.loads(exec_resp.read().decode('utf-8'))
        print('Execution ID:', exec_res.get('executionId'))
        print('Output Parameters:')
        print(json.dumps(exec_res.get('outputParameters', {}), indent=2))
except urllib.error.HTTPError as e:
    print('Execute HTTPError:', e.code, e.read().decode())
