import json
import urllib.request
import urllib.error
import google.auth
import google.auth.transport.requests

PROJECT_ID = 'proj-prod-app1-439018'
LOCATION = 'us-central1'
INTEGRATION_NAME = 'drive_claims_to_sheets'

creds, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
creds.refresh(google.auth.transport.requests.Request())

headers = {
    'Authorization': f'Bearer {creds.token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

with open('drive_claims_integration.json', 'r') as f:
    version_dict = json.load(f)

upload_body = {
    'content': json.dumps(version_dict),
    'fileFormat': 'JSON'
}

base_url = f'https://integrations.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/integrations/{INTEGRATION_NAME}'
upload_url = f'{base_url}/versions:upload'

print(f"Uploading new integration draft to: {upload_url}...")
req = urllib.request.Request(upload_url, data=json.dumps(upload_body).encode('utf-8'), headers=headers, method='POST')

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        vname = res['integrationVersion']['name']
        vid = vname.split('/')[-1]
        print('Upload successful! Version ID:', vid)
        
        # Publish version
        pub_url = f'{base_url}/versions/{vid}:publish'
        print(f"Publishing version {vid}...")
        pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(pub_req) as pub_resp:
            print('Publish successful! Active version:', vid)
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
