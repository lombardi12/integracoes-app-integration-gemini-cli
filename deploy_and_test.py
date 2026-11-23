import json
import urllib.request
import urllib.error
import google.auth
import google.auth.transport.requests

creds, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
creds.refresh(google.auth.transport.requests.Request())
headers = {
    'Authorization': f'Bearer {creds.token}',
    'User-Agent': 'agent-skills/1.0 (skill:application-integration-authoring)',
    'Content-Type': 'application/json'
}

js_code = """function executesScript(event) {
  var payload = event.getParameter('salesforce_payload');
  if (typeof payload === 'string' && payload.length > 0) {
    try { payload = JSON.parse(payload); } catch (e) {}
  }
  payload = payload || {};

  var oppId = payload.Id || payload.opportunity_id || event.getParameter('opportunity_id') || ('OPP-' + Date.now());
  var oppName = payload.Name || payload.opportunity_name || event.getParameter('opportunity_name') || 'Sample Opportunity';
  var amount = Number(payload.Amount !== undefined ? payload.Amount : (payload.amount !== undefined ? payload.amount : (event.getParameter('amount') || 0)));
  var stage = payload.StageName || payload.stage_name || event.getParameter('stage_name') || 'Prospecting';
  var closeDate = payload.CloseDate || payload.close_date || event.getParameter('close_date') || new Date().toISOString().split('T')[0];
  var changeType = (payload.ChangeEventHeader && payload.ChangeEventHeader.changeType) || payload.change_type || 'CREATE';
  var ingestedAt = new Date().toISOString();

  var row = {
    opportunity_id: oppId,
    opportunity_name: oppName,
    amount: amount,
    stage_name: stage,
    close_date: closeDate,
    change_type: changeType,
    ingested_at: ingestedAt
  };

  var bqPayload = {
    kind: 'bigquery#tableDataInsertAllRequest',
    rows: [
      {
        json: row
      }
    ]
  };

  event.setParameter('bq_request_body', JSON.stringify(bqPayload));
  event.setParameter('opportunity_id', oppId);
  event.setParameter('opportunity_name', oppName);
  event.setParameter('amount', amount);
  event.setParameter('stage_name', stage);
  event.setParameter('status', 'TRANSFORMED');
}

function executeScript(event) {
  executesScript(event);
}
"""

version_dict = {
  'description': 'Salesforce Opportunity to BigQuery staging via REST API',
  'runAsServiceAccount': '1023905883743-compute@developer.gserviceaccount.com',
  'triggerConfigs': [
    {
      'label': 'Salesforce Opportunity Test Trigger',
      'triggerType': 'API',
      'triggerNumber': '1',
      'triggerId': 'api_trigger/salesforce_opportunity_test',
      'properties': {
        'Trigger name': 'salesforce_opportunity_test'
      },
      'startTasks': [
        {
          'taskId': '1'
        }
      ],
      'inputVariables': {
        'names': ['salesforce_payload', 'opportunity_id', 'opportunity_name', 'amount', 'stage_name', 'close_date']
      },
      'outputVariables': {
        'names': ['opportunity_id', 'opportunity_name', 'amount', 'stage_name', 'status']
      }
    }
  ],
  'taskConfigs': [
    {
      'task': 'JavaScriptTask',
      'taskId': '1',
      'displayName': 'Transform Opportunity for BigQuery',
      'taskExecutionStrategy': 'WHEN_ALL_SUCCEED',
      'nextTasks': [
        {
          'taskId': '2'
        }
      ],
      'parameters': {
        'javaScriptEngine': {
          'key': 'javaScriptEngine',
          'value': {
            'stringValue': 'V8'
          }
        },
        'script': {
          'key': 'script',
          'value': {
            'stringValue': js_code
          }
        }
      }
    },
    {
      'task': 'GenericRestV2Task',
      'taskId': '2',
      'displayName': 'Insert into BigQuery',
      'taskExecutionStrategy': 'WHEN_ALL_SUCCEED',
      'parameters': {
        'throwError': {
          'key': 'throwError',
          'value': {
            'booleanValue': False
          }
        },
        'responseBody': {
          'key': 'responseBody',
          'value': {
            'stringArray': {
              'stringValues': ['$`Task_2_responseBody`$']
            }
          }
        },
        'disableSSLValidation': {
          'key': 'disableSSLValidation',
          'value': {
            'booleanValue': False
          }
        },
        'httpParams': {
          'key': 'httpParams'
        },
        'responseHeader': {
          'key': 'responseHeader',
          'value': {
            'stringArray': {
              'stringValues': ['$`Task_2_responseHeader`$']
            }
          }
        },
        'userAgent': {
          'key': 'userAgent',
          'value': {
            'stringValue': ''
          }
        },
        'httpMethod': {
          'key': 'httpMethod',
          'value': {
            'stringValue': 'POST'
          }
        },
        'responseStatus': {
          'key': 'responseStatus',
          'value': {
            'stringArray': {
              'stringValues': ['$`Task_2_responseStatus`$']
            }
          }
        },
        'url': {
          'key': 'url',
          'value': {
            'stringValue': 'https://bigquery.googleapis.com/bigquery/v2/projects/proj-prod-app1-439018/datasets/salesforce_staging/tables/opportunities/insertAll'
          }
        },
        'urlFetchingService': {
          'key': 'urlFetchingService',
          'value': {
            'stringValue': 'HARPOON'
          }
        },
        'useSSL': {
          'key': 'useSSL',
          'value': {
            'booleanValue': False
          }
        },
        'requestorId': {
          'key': 'requestorId',
          'value': {
            'stringValue': ''
          }
        },
        'urlQueryStrings': {
          'key': 'urlQueryStrings'
        },
        'requestBody': {
          'key': 'requestBody',
          'value': {
            'stringValue': '$bq_request_body$'
          }
        },
        'followRedirects': {
          'key': 'followRedirects',
          'value': {
            'booleanValue': True
          }
        },
        'additionalHeaders': {
          'key': 'additionalHeaders'
        }
      }
    }
  ],
  'integrationParameters': [
    {
      'key': 'salesforce_payload',
      'dataType': 'JSON_VALUE',
      'inputOutputType': 'IN'
    },
    {
      'key': 'opportunity_id',
      'dataType': 'STRING_VALUE',
      'inputOutputType': 'IN_OUT',
      'defaultValue': {'stringValue': ''}
    },
    {
      'key': 'opportunity_name',
      'dataType': 'STRING_VALUE',
      'inputOutputType': 'IN_OUT',
      'defaultValue': {'stringValue': ''}
    },
    {
      'key': 'amount',
      'dataType': 'DOUBLE_VALUE',
      'inputOutputType': 'IN_OUT',
      'defaultValue': {'doubleValue': 0.0}
    },
    {
      'key': 'stage_name',
      'dataType': 'STRING_VALUE',
      'inputOutputType': 'IN_OUT',
      'defaultValue': {'stringValue': ''}
    },
    {
      'key': 'close_date',
      'dataType': 'STRING_VALUE',
      'inputOutputType': 'IN_OUT',
      'defaultValue': {'stringValue': ''}
    },
    {
      'key': 'bq_request_body',
      'dataType': 'STRING_VALUE',
      'inputOutputType': 'IN_OUT',
      'defaultValue': {'stringValue': ''}
    },
    {
      'key': 'status',
      'dataType': 'STRING_VALUE',
      'inputOutputType': 'OUT',
      'defaultValue': {'stringValue': ''}
    },
    {
      'key': '`Task_2_responseBody`',
      'dataType': 'STRING_VALUE',
      'displayName': '`Task_2_responseBody`',
      'isTransient': True,
      'producer': '1_2'
    },
    {
      'key': '`Task_2_responseHeader`',
      'dataType': 'STRING_VALUE',
      'displayName': '`Task_2_responseHeader`',
      'isTransient': True,
      'producer': '1_2'
    },
    {
      'key': '`Task_2_responseStatus`',
      'dataType': 'STRING_VALUE',
      'displayName': '`Task_2_responseStatus`',
      'isTransient': True,
      'producer': '1_2'
    }
  ]
}

upload_body = {
    'content': json.dumps(version_dict),
    'fileFormat': 'JSON'
}

url = 'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/salesforce_opportunity_to_bigquery/versions:upload'
req = urllib.request.Request(url, data=json.dumps(upload_body).encode('utf-8'), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        vname = res['integrationVersion']['name']
        vid = vname.split('/')[-1]
        print('Upload successful! Version ID:', vid)
        
        # Now publish
        pub_url = f'https://integrations.googleapis.com/v1/projects/proj-prod-app1-439018/locations/us-central1/integrations/salesforce_opportunity_to_bigquery/versions/{vid}:publish'
        pub_req = urllib.request.Request(pub_url, data=json.dumps({'configParameters': {}}).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(pub_req) as pub_resp:
            print('Publish successful! Active version:', vid)
except urllib.error.HTTPError as e:
    print('HTTPError:', e.code, e.read().decode('utf-8'))
except Exception as e:
    print('Error:', e)
