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

auth_config_id = 'e2bbf6a3-8d6b-43a4-a491-5011bc9bee1e'
auth_proto_value = json.dumps({
    '@type': 'type.googleapis.com/enterprise.crm.eventbus.authconfig.AuthConfigTaskParam',
    'authConfigId': auth_config_id
})

with open('drive_claims_integration.json') as f:
    v = json.load(f)

v['runAsServiceAccount'] = 'appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com'

# 1. Update Task 1 URL to exclude folders
for t in v['taskConfigs']:
    if t['taskId'] == '1':
        t['parameters']['url']['value']['stringValue'] = (
            "https://www.googleapis.com/drive/v3/files?q='14dZ6mA6hNNOqxixI679NG2mSCG6g_dMO'+in+parents+and+mimeType!=%27application/vnd.google-apps.folder%27+and+trashed=false"
        )
        t['parameters']['authConfig'] = {'key': 'authConfig', 'value': {'jsonValue': auth_proto_value}}

# 2. Update Task 2 to store file_id
for t in v['taskConfigs']:
    if t['taskId'] == '2':
        t['parameters']['script']['value']['stringValue'] = """function executeScript(event) {
  var rawDriveResp = event.getParameter('`Task_1_responseBody`') || event.getParameter('Task_1_responseBody') || '';
  var inputDocName = event.getParameter('document_name') || '';
  var inputDocContent = event.getParameter('document_content') || '';
  
  var hasFileToDownload = false;
  var hasDocToProcess = false;
  var downloadUrl = '';
  var docName = inputDocName || 'Documento';
  var fileId = '';
  
  if (typeof rawDriveResp === 'string' && rawDriveResp.length > 0) {
    try {
      var d = JSON.parse(rawDriveResp);
      if (d.files && Array.isArray(d.files) && d.files.length > 0) {
        var firstFile = d.files[0];
        fileId = firstFile.id;
        docName = firstFile.name;
        downloadUrl = 'https://www.googleapis.com/drive/v3/files/' + fileId + '?alt=media';
        hasFileToDownload = true;
        hasDocToProcess = true;
      }
    } catch (e) {}
  }
  
  if (!hasDocToProcess && typeof inputDocContent === 'string' && inputDocContent.length > 0) {
    hasDocToProcess = true;
  }
  
  event.setParameter('file_id', fileId);
  event.setParameter('document_name', docName);
  event.setParameter('drive_download_url', downloadUrl);
  event.setParameter('has_file_to_download', hasFileToDownload);
  event.setParameter('has_document_to_process', hasDocToProcess);
}
var executesScript = executeScript;"""

# 3. Add file_id to integrationParameters if not present
param_keys = {p['key'] for p in v.get('integrationParameters', [])}
if 'file_id' not in param_keys:
    v['integrationParameters'].append({
        'key': 'file_id',
        'dataType': 'STRING_VALUE',
        'inputOutputType': 'IN_OUT_TYPE_UNSPECIFIED'
    })
if '`Task_9_responseBody`' not in param_keys:
    v['integrationParameters'].append({'key': '`Task_9_responseBody`', 'dataType': 'STRING_VALUE', 'inputOutputType': 'IN_OUT_TYPE_UNSPECIFIED'})
    v['integrationParameters'].append({'key': '`Task_9_responseHeader`', 'dataType': 'STRING_VALUE', 'inputOutputType': 'IN_OUT_TYPE_UNSPECIFIED'})
    v['integrationParameters'].append({'key': '`Task_9_responseStatus`', 'dataType': 'STRING_VALUE', 'inputOutputType': 'IN_OUT_TYPE_UNSPECIFIED'})

# 4. Add Task 9: Move Processed File to Subfolder
task9 = {
    'task': 'GenericRestV2Task',
    'taskId': '9',
    'displayName': 'Move Processed File to Subfolder',
    'taskExecutionStrategy': 'WHEN_ALL_SUCCEED',
    'parameters': {
        'throwError': {'key': 'throwError', 'value': {'booleanValue': False}},
        'responseBody': {'key': 'responseBody', 'value': {'stringArray': {'stringValues': ['$`Task_9_responseBody`$']}}},
        'responseHeader': {'key': 'responseHeader', 'value': {'stringArray': {'stringValues': ['$`Task_9_responseHeader`$']}}},
        'responseStatus': {'key': 'responseStatus', 'value': {'stringArray': {'stringValues': ['$`Task_9_responseStatus`$']}}},
        'userAgent': {'key': 'userAgent', 'value': {'stringValue': ''}},
        'httpMethod': {'key': 'httpMethod', 'value': {'stringValue': 'PATCH'}},
        'url': {'key': 'url', 'value': {'stringValue': "https://www.googleapis.com/drive/v3/files/$file_id$?addParents=1L1-U8pKxw0HovNW8P2T0-c9DwosiCKcZ&removeParents=14dZ6mA6hNNOqxixI679NG2mSCG6g_dMO"}},
        'urlFetchingService': {'key': 'urlFetchingService', 'value': {'stringValue': 'HARPOON'}},
        'useSSL': {'key': 'useSSL', 'value': {'booleanValue': False}},
        'disableSSLValidation': {'key': 'disableSSLValidation', 'value': {'booleanValue': False}},
        'followRedirects': {'key': 'followRedirects', 'value': {'booleanValue': True}},
        'requestorId': {'key': 'requestorId', 'value': {'stringValue': ''}},
        'authConfig': {'key': 'authConfig', 'value': {'jsonValue': auth_proto_value}},
        'requestBody': {'key': 'requestBody', 'value': {'stringValue': '{}'}},
        'httpParams': {'key': 'httpParams'},
        'urlQueryStrings': {'key': 'urlQueryStrings'},
        'additionalHeaders': {'key': 'additionalHeaders'}
    }
}

# Check if Task 9 already exists
task_ids = {t['taskId'] for t in v['taskConfigs']}
if '9' not in task_ids:
    v['taskConfigs'].append(task9)

# Connect Task 8 to Task 9 with condition has_file_to_download == true
for t in v['taskConfigs']:
    if t['taskId'] == '8':
        t['nextTasks'] = [
            {
                'taskId': '9',
                'condition': '$has_file_to_download$ = true',
                'displayName': 'If file came from Drive'
            }
        ]

# 5. Ensure Triggers have both API and CRON
v['triggerConfigs'] = [
    {
        'label': 'API Trigger Claims Processor',
        'triggerType': 'API',
        'triggerNumber': '1',
        'triggerId': 'api_trigger/drive_claims_processor',
        'properties': {'Trigger name': 'drive_claims_processor'},
        'startTasks': [{'taskId': '1'}],
        'outputVariables': {
            'names': [
                'document_name',
                'acima_de_mil',
                'valor_causa',
                'analysis_result',
                'sheets_status',
                'status'
            ]
        }
    },
    {
        'label': 'Schedule Check Every 15 Min',
        'triggerType': 'CRON',
        'triggerNumber': '2',
        'triggerId': 'cron_trigger/drive_claims_schedule',
        'properties': {
            'Timer Name': 'drive_claims_schedule',
            'Scheduled Time spec': '*/15 * * * *'
        },
        'startTasks': [{'taskId': '1'}]
    }
]

# Write back formatted JSON
with open('drive_claims_integration.json', 'w') as f:
    json.dump(v, f, indent=2, ensure_ascii=False)

print('Updated drive_claims_integration.json with full pipeline.')

# Deploy and publish
token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

upload_body = {
    'content': json.dumps(v),
    'fileFormat': 'JSON'
}

url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions:upload'
req = urllib.request.Request(url, data=json.dumps(upload_body).encode(), headers=headers, method='POST')
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    vid = res['integrationVersion']['name'].split('/')[-1]
    print('Uploaded Final Version ID:', vid)

pub_url = f'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions/{vid}:publish'
pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
with urllib.request.urlopen(pub_req) as pub_resp:
    print('Published final status:', pub_resp.status)
