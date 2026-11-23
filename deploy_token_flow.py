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

with open('drive_claims_integration.json') as f:
    v = json.load(f)

# Update runAsServiceAccount
v['runAsServiceAccount'] = 'appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com'

# Add workspace_auth_header to integrationParameters
existing_keys = {p['key'] for p in v.get('integrationParameters', [])}
for k in ['workspace_auth_header', '`Task_10_responseBody`', '`Task_10_responseHeader`', '`Task_10_responseStatus`']:
    if k not in existing_keys:
        v['integrationParameters'].append({
            'key': k,
            'dataType': 'STRING_VALUE',
            'inputOutputType': 'IN_OUT_TYPE_UNSPECIFIED'
        })

# Task 10: Generate Workspace Token via iamcredentials
task10 = {
    'task': 'GenericRestV2Task',
    'taskId': '10',
    'displayName': 'Generate Workspace Token',
    'taskExecutionStrategy': 'WHEN_ALL_SUCCEED',
    'nextTasks': [{'taskId': '11'}],
    'parameters': {
        'throwError': {'key': 'throwError', 'value': {'booleanValue': False}},
        'responseBody': {'key': 'responseBody', 'value': {'stringArray': {'stringValues': ['$`Task_10_responseBody`$']}}},
        'responseHeader': {'key': 'responseHeader', 'value': {'stringArray': {'stringValues': ['$`Task_10_responseHeader`$']}}},
        'responseStatus': {'key': 'responseStatus', 'value': {'stringArray': {'stringValues': ['$`Task_10_responseStatus`$']}}},
        'userAgent': {'key': 'userAgent', 'value': {'stringValue': ''}},
        'httpMethod': {'key': 'httpMethod', 'value': {'stringValue': 'POST'}},
        'url': {'key': 'url', 'value': {'stringValue': 'https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com:generateAccessToken'}},
        'urlFetchingService': {'key': 'urlFetchingService', 'value': {'stringValue': 'HARPOON'}},
        'useSSL': {'key': 'useSSL', 'value': {'booleanValue': False}},
        'disableSSLValidation': {'key': 'disableSSLValidation', 'value': {'booleanValue': False}},
        'followRedirects': {'key': 'followRedirects', 'value': {'booleanValue': True}},
        'requestorId': {'key': 'requestorId', 'value': {'stringValue': ''}},
        'requestBody': {'key': 'requestBody', 'value': {'stringValue': '{"scope": ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]}'}},
        'httpParams': {'key': 'httpParams'},
        'urlQueryStrings': {'key': 'urlQueryStrings'},
        'additionalHeaders': {'key': 'additionalHeaders'}
    }
}

# Task 11: Extract Token and Prepare Header
js_code = """function executeScript(event) {
  var rawBody = event.getParameter('`Task_10_responseBody`') || event.getParameter('Task_10_responseBody') || '';
  var token = '';
  if (typeof rawBody === 'string' && rawBody.length > 0) {
    try {
      var d = JSON.parse(rawBody);
      token = d.accessToken || '';
    } catch (e) {}
  }
  var h = {};
  if (token) {
    h['Authorization'] = 'Bearer ' + token;
  }
  event.setParameter('workspace_auth_header', JSON.stringify(h));
}
var executesScript = executeScript;"""

task11 = {
    'task': 'JavaScriptTask',
    'taskId': '11',
    'displayName': 'Extract Workspace Token',
    'taskExecutionStrategy': 'WHEN_ALL_SUCCEED',
    'nextTasks': [{'taskId': '1'}],
    'parameters': {
        'script': {
            'key': 'script',
            'value': {
                'stringValue': js_code
            }
        }
    }
}

# Update trigger startTasks to task 10
v['triggerConfigs'][0]['startTasks'] = [{'taskId': '10'}]

# Insert tasks 10 and 11
v['taskConfigs'].insert(0, task10)
v['taskConfigs'].insert(1, task11)

# In tasks 1, 3, and 7, set additionalHeaders to $workspace_auth_header$
for t in v['taskConfigs']:
    if t.get('task') == 'JavaScriptTask':
        script_val = t['parameters']['script']['value']['stringValue']
        if 'function executeScript' not in script_val:
            script_val += "\nfunction executeScript(event) { return executesScript(event); }\n"
            t['parameters']['script']['value']['stringValue'] = script_val
    if t['taskId'] in ['1', '3', '7']:
        if 'authConfig' in t['parameters']:
            del t['parameters']['authConfig']
        t['parameters']['additionalHeaders'] = {
            'key': 'workspace_auth_header'
        }

upload_body = {
    'content': json.dumps(v),
    'fileFormat': 'JSON'
}

url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions:upload'
req = urllib.request.Request(url, data=json.dumps(upload_body).encode(), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        vname = res['integrationVersion']['name']
        vid = vname.split('/')[-1]
        print('Uploaded Version ID:', vid)
        
        # Publish
        pub_url = f'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions/{vid}:publish'
        pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(pub_req) as pub_resp:
            print('Published status:', pub_resp.status)
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode())
