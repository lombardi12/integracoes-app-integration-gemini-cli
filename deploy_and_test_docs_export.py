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

with open('drive_claims_integration.json') as f:
    v = json.load(f)

token = subprocess.check_output(['gcloud', 'auth', 'print-access-token']).decode().strip()
headers = {
    'Authorization': f'Bearer {token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

# 1. Upload draft version
upload_body = {
    'content': json.dumps(v),
    'fileFormat': 'JSON'
}
upload_url = f'https://integrations.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/integrations/{INTEGRATION_NAME}/versions:upload'
req = urllib.request.Request(upload_url, data=json.dumps(upload_body).encode(), headers=headers, method='POST')

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())
    version_name = res['integrationVersion']['name']
    vid = version_name.split('/')[-1]
    print('Uploaded Version ID:', vid)

# 2. Publish draft version
pub_url = f'https://integrations.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/integrations/{INTEGRATION_NAME}/versions/{vid}:publish'
pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
with urllib.request.urlopen(pub_req) as pub_resp:
    print('Published status:', pub_resp.status)

print(f'Integration {INTEGRATION_NAME} successfully updated and published with version {vid}.')
