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
import urllib.error
import google.auth
import google.auth.transport.requests
from google.cloud import bigquery

creds, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
creds.refresh(google.auth.transport.requests.Request())
headers = {
    'Authorization': f'Bearer {creds.token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

# Simulated Salesforce Opportunity CDC Event
salesforce_mock_payload = {
    "ChangeEventHeader": {
        "commitNumber": 12345678,
        "commitUser": "0055g0000012XYZ",
        "sequenceNumber": 1,
        "entityName": "Opportunity",
        "changeType": "CREATE",
        "changeOrigin": "com/salesforce/api/soap",
        "transactionKey": "0001-tx-key"
    },
    "Id": "0065g0000021ABCQAZ",
    "Name": "Acme - Expansao Cloud 2026",
    "Amount": 150000.0,
    "StageName": "Closed Won",
    "CloseDate": "2026-11-30"
}

execute_body = {
    "triggerId": "api_trigger/salesforce_opportunity_test",
    "inputParameters": {
        "salesforce_payload": {
            "jsonValue": json.dumps(salesforce_mock_payload)
        }
    }
}

exec_url = "https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/salesforce_opportunity_to_bigquery:execute"
req = urllib.request.Request(exec_url, data=json.dumps(execute_body).encode('utf-8'), headers=headers, method='POST')

print("Invoking salesforce_opportunity_to_bigquery:execute...")
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("Execution ID:", res.get("executionId"))
        print("Output parameters:", json.dumps(res.get("outputParameters", {}), indent=2))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)

# Now query BigQuery to verify insertion
print("\nChecking BigQuery table salesforce_staging.opportunities...")
bq_client = bigquery.Client(project="proj-prod-app1-439018")
query = "SELECT opportunity_id, opportunity_name, amount, stage_name, close_date, change_type, ingested_at FROM `proj-prod-app1-439018.salesforce_staging.opportunities` ORDER BY ingested_at DESC LIMIT 5"
rows = list(bq_client.query(query).result())
print(f"Total rows retrieved: {len(rows)}")
for r in rows:
    print(dict(r))
