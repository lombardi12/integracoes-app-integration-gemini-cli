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
    'description': 'Test Connectors Task for Google Drive',
    'runAsServiceAccount': 'appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com',
    'triggerConfigs': [
        {
            'label': 'Test Trigger',
            'triggerType': 'API',
            'triggerNumber': '1',
            'triggerId': 'api_trigger/test_drive_conn',
            'properties': {
                'Trigger name': 'test_drive_conn'
            },
            'startTasks': [{'taskId': '1'}],
            'outputVariables': {'names': ['`Task_1_connectorOutputPayload`']}
        }
    ],
    'taskConfigs': [
        {
            'task': 'GenericConnectorTask',
            'taskId': '1',
            'displayName': 'List Drive Files via Connector',
            'parameters': {
                'connectionName': {
                    'key': 'connectionName',
                    'value': {
                        'stringValue': 'projects/proj-prod-app1-439018/locations/us-central1/connections/drive-claims-conn'
                    }
                },
                'operation': {
                    'key': 'operation',
                    'value': {
                        'stringValue': 'LIST_ENTITIES'
                    }
                },
                'entityType': {
                    'key': 'entityType',
                    'value': {
                        'stringValue': 'Files'
                    }
                },
                'filterClause': {
                    'key': 'filterClause',
                    'value': {
                        'stringValue': "'14dZ6mA6hNNOqxixI679NG2mSCG6g_dMO' in parents and trashed = false"
                    }
                },
                'connectorOutputPayload': {
                    'key': 'connectorOutputPayload',
                    'value': {
                        'stringValue': '$`Task_1_connectorOutputPayload`$'
                    }
                }
            }
        }
    ],
    'integrationParameters': [
        {
            'key': '`Task_1_connectorOutputPayload`',
            'dataType': 'STRING_VALUE',
            'inputOutputType': 'OUT'
        }
    ]
}

url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions:upload'
req = urllib.request.Request(url, data=json.dumps({'content': json.dumps(test_int), 'fileFormat': 'JSON'}).encode(), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        vid = res['integrationVersion']['name'].split('/')[-1]
        print('Uploaded test draft version:', vid)
        
        # Publish
        pub_url = f'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions/{vid}:publish'
        pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(pub_req) as pub_resp:
            print('Published test version!')
            
        # Execute test
        exec_url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets:execute'
        exec_payload = {'triggerId': 'api_trigger/test_drive_conn'}
        exec_req = urllib.request.Request(exec_url, data=json.dumps(exec_payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(exec_req) as exec_resp:
            exec_res = json.loads(exec_resp.read().decode('utf-8'))
            print('Execution ID:', exec_res.get('executionId'))
            print('Output Parameters:')
            print(json.dumps(exec_res.get('outputParameters', {}), indent=2))
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
