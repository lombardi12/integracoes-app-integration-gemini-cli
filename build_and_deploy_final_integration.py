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

# Update runAsServiceAccount
v['runAsServiceAccount'] = 'appint-drive-sheets@proj-prod-app1-439018.iam.gserviceaccount.com'

# Ensure authConfig on tasks 1, 3, and 7
for t in v['taskConfigs']:
    # Clean up additionalHeaders
    if 'additionalHeaders' in t.get('parameters', {}):
        t['parameters']['additionalHeaders'] = {'key': 'additionalHeaders'}
    
    if t['taskId'] in ['1', '3', '7']:
        t['parameters']['authConfig'] = {
            'key': 'authConfig',
            'value': {
                'jsonValue': auth_proto_value
            }
        }
    
    # Ensure JavaScript tasks define both executeScript and executesScript
    if t.get('task') == 'JavaScriptTask':
        s = t['parameters']['script']['value']['stringValue']
        if 'function executeScript' not in s:
            s += '\nfunction executeScript(event) { return executesScript(event); }\n'
        if 'var executesScript = executeScript;' not in s and 'function executesScript' not in s:
            s += '\nvar executesScript = executeScript;\n'
        t['parameters']['script']['value']['stringValue'] = s

# Write back formatted JSON
with open('drive_claims_integration.json', 'w') as f:
    json.dump(v, f, indent=2, ensure_ascii=False)

print('Updated drive_claims_integration.json successfully.')

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
    print('Uploaded Version ID:', vid)

pub_url = f'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/drive_claims_to_sheets/versions/{vid}:publish'
pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
with urllib.request.urlopen(pub_req) as pub_resp:
    print('Published status:', pub_resp.status)
