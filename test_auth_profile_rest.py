import urllib.request
import json
import subprocess

token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

auth_full = 'projects/1023905883743/locations/us-central1/authConfigs/e2bbf6a3-8d6b-43a4-a491-5011bc9bee1e'

test_int = {
    'description': 'Test AuthConfig on GenericRestV2Task for Sheets',
    'runAsServiceAccount': 'appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com',
    'triggerConfigs': [
        {
            'label': 'Test Trigger Sheets REST',
            'triggerType': 'API',
            'triggerNumber': '1',
            'triggerId': 'api_trigger/test_sheets_rest',
            'properties': {'Trigger name': 'test_sheets_rest'},
            'startTasks': [{'taskId': '1'}],
            'outputVariables': {'names': ['`Task_1_responseBody`', '`Task_1_responseStatus`']}
        }
    ],
    'taskConfigs': [
        {
            'task': 'GenericRestV2Task',
            'taskId': '1',
            'displayName': 'Append Claim to Google Sheets',
            'parameters': {
                'throwError': {'key': 'throwError', 'value': {'booleanValue': False}},
                'responseBody': {'key': 'responseBody', 'value': {'stringArray': {'stringValues': ['$`Task_1_responseBody`$']}}},
                'responseHeader': {'key': 'responseHeader', 'value': {'stringArray': {'stringValues': ['$`Task_1_responseHeader`$']}}},
                'responseStatus': {'key': 'responseStatus', 'value': {'stringArray': {'stringValues': ['$`Task_1_responseStatus`$']}}},
                'userAgent': {'key': 'userAgent', 'value': {'stringValue': ''}},
                'httpMethod': {'key': 'httpMethod', 'value': {'stringValue': 'POST'}},
                'url': {'key': 'url', 'value': {'stringValue': 'https://sheets.googleapis.com/v4/spreadsheets/1mjqIz1LvNwyZSj1_LTfKcMVbb4jDIULjNb-YQmkrKr8/values/Sheet1!A1:append?valueInputOption=USER_ENTERED'}},
                'urlFetchingService': {'key': 'urlFetchingService', 'value': {'stringValue': 'HARPOON'}},
                'useSSL': {'key': 'useSSL', 'value': {'booleanValue': False}},
                'disableSSLValidation': {'key': 'disableSSLValidation', 'value': {'booleanValue': False}},
                'followRedirects': {'key': 'followRedirects', 'value': {'booleanValue': True}},
                'requestorId': {'key': 'requestorId', 'value': {'stringValue': ''}},
                'authConfig': {
                    'key': 'authConfig',
                    'value': {
                        'jsonValue': json.dumps({
                            '@type': 'type.googleapis.com/enterprise.crm.eventbus.authconfig.AuthConfigTaskParam',
                            'authConfigId': 'e2bbf6a3-8d6b-43a4-a491-5011bc9bee1e'
                        })
                    }
                },
                'requestBody': {
                    'key': 'requestBody',
                    'value': {
                        'stringValue': json.dumps({
                            'range': 'Sheet1!A1',
                            'majorDimension': 'ROWS',
                            'values': [
                                ['20/11/2026 01:50', 'Peticao_Inicial_Cobranca_001.pdf', 'Petição Inicial', '1045231-88.2026.8.26.0100', 'Carlos Eduardo Pereira', 'Banco Soluções Financeiras S/A', 12500, 'Via AuthConfig REST']
                            ]
                        })
                    }
                },
                'httpParams': {'key': 'httpParams'},
                'urlQueryStrings': {'key': 'urlQueryStrings'},
                'additionalHeaders': {'key': 'additionalHeaders'}
            }
        }
    ],
    'integrationParameters': [
        {'key': '`Task_1_responseBody`', 'dataType': 'STRING_VALUE', 'inputOutputType': 'OUT'},
        {'key': '`Task_1_responseHeader`', 'dataType': 'STRING_VALUE', 'inputOutputType': 'OUT'},
        {'key': '`Task_1_responseStatus`', 'dataType': 'STRING_VALUE', 'inputOutputType': 'OUT'}
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
exec_payload = {'triggerId': 'api_trigger/test_sheets_rest'}
exec_req = urllib.request.Request(exec_url, data=json.dumps(exec_payload).encode('utf-8'), headers=headers, method='POST')
try:
    with urllib.request.urlopen(exec_req) as exec_resp:
        exec_res = json.loads(exec_resp.read().decode('utf-8'))
        print('Execution ID:', exec_res.get('executionId'))
        print('Output Parameters:')
        print(json.dumps(exec_res.get('outputParameters', {}), indent=2))
except urllib.error.HTTPError as e:
    print('Execute HTTPError:', e.code, e.read().decode())
