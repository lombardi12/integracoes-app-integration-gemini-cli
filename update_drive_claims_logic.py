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

with open('drive_claims_integration.json') as f:
    d = json.load(f)

for t in d['taskConfigs']:
    if t.get('taskId') == '2':
        script_2 = """function executeScript(event) {
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
      var data = JSON.parse(rawDriveResp);
      if (data.files && Array.isArray(data.files) && data.files.length > 0) {
        var firstFile = data.files[0];
        fileId = firstFile.id;
        docName = firstFile.name;
        var mimeType = firstFile.mimeType || '';
        
        if (mimeType === 'application/vnd.google-apps.document') {
          downloadUrl = 'https://www.googleapis.com/drive/v3/files/' + fileId + '/export?mimeType=text/plain';
        } else {
          downloadUrl = 'https://www.googleapis.com/drive/v3/files/' + fileId + '?alt=media';
        }
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
var executesScript = executeScript;
"""
        t['parameters']['script']['value']['stringValue'] = script_2

    if t.get('taskId') == '6':
        script_6 = """function executesScript(event) {
  var agentRespRaw = event.getParameter('`Task_5_responseBody`') || event.getParameter('Task_5_responseBody') || '';
  var docName = event.getParameter('document_name') || 'Documento';
  
  var result = null;
  
  if (typeof agentRespRaw === 'string' && agentRespRaw.length > 0) {
    var lines = agentRespRaw.split('\\n');
    var cleanedLines = [];
    for (var i = 0; i < lines.length; i++) {
      var l = lines[i].replace(/\\r/g, '').trim();
      if (l.indexOf('data:') === 0) {
        cleanedLines.push(l.substring(5).trim());
      } else if (l === '') {
        cleanedLines.push('---EVENT_BOUNDARY---');
      }
    }
    
    var events = cleanedLines.join('\\n').split('---EVENT_BOUNDARY---');
    for (var j = events.length - 1; j >= 0; j--) {
      var ev = events[j].trim();
      if (!ev) continue;
      try {
        var obj = JSON.parse(ev);
        var text = '';
        if (obj.artifactUpdate && obj.artifactUpdate.artifact && obj.artifactUpdate.artifact.parts) {
          text = obj.artifactUpdate.artifact.parts[0].text;
        } else if (obj.statusUpdate && obj.statusUpdate.status && obj.statusUpdate.status.message && obj.statusUpdate.status.message.content) {
          text = obj.statusUpdate.status.message.content[0].text;
        }
        if (text && text.indexOf('acima_de_mil') !== -1) {
          var cleanText = text.replace(/```json/g, '').replace(/```/g, '').trim();
          result = JSON.parse(cleanText);
          break;
        }
      } catch (e) {}
    }
  }

  if (!result && typeof agentRespRaw === 'string') {
    try {
      var parsed = JSON.parse(agentRespRaw);
      if (parsed.acima_de_mil !== undefined) {
        result = parsed;
      }
    } catch (e) {}
  }

  if (!result) {
    event.setParameter('status', 'ERROR_PARSING_AGENT_RESPONSE');
    event.setParameter('should_append_sheets', false);
    return;
  }

  var rawVal = result.valor_causa;
  var valorCausa = 0;
  if (typeof rawVal === 'number') {
    valorCausa = rawVal;
  } else if (typeof rawVal === 'string') {
    var cleaned = rawVal.replace(/[^\\d.,]/g, '').trim();
    if (cleaned.indexOf(',') !== -1 && cleaned.indexOf('.') !== -1) {
      cleaned = cleaned.replace(/\\./g, '').replace(',', '.');
    } else if (cleaned.indexOf(',') !== -1) {
      cleaned = cleaned.replace(',', '.');
    }
    var num = parseFloat(cleaned);
    valorCausa = isNaN(num) ? 0 : num;
  }

  var acimaDeMil = (result.acima_de_mil === true || valorCausa > 1000);

  event.setParameter('valor_causa', valorCausa);
  event.setParameter('acima_de_mil', acimaDeMil);
  event.setParameter('analysis_result', JSON.stringify(result));

  var resumo = (result.resumo_pedido || '').toLowerCase();
  var isBinaryError = (resumo.indexOf('binário') !== -1 || resumo.indexOf('ilegível') !== -1 || resumo.indexOf('.docx') !== -1);

  if (isBinaryError) {
    event.setParameter('should_append_sheets', false);
    event.setParameter('status', 'ERROR_UNREADABLE_FILE_FORMAT');
  } else if (acimaDeMil) {
    event.setParameter('should_append_sheets', true);
    event.setParameter('status', 'CLAIM_EXCEEDS_1000_RECORDING_TO_SHEETS');

    var nowIso = new Date().toISOString();
    var row = [
      nowIso,
      docName,
      result.tipo_documento || 'Petição',
      result.numero_processo || 'Não identificado',
      result.autor || 'Não informado',
      result.reu || 'Não informado',
      valorCausa,
      result.resumo_pedido || ''
    ];

    var sheetsPayload = {
      range: 'Sheet1!A1',
      majorDimension: 'ROWS',
      values: [row]
    };

    event.setParameter('sheets_append_body', JSON.stringify(sheetsPayload));
  } else {
    event.setParameter('should_append_sheets', false);
    event.setParameter('status', 'CLAIM_UNDER_OR_EQUAL_1000_IGNORED');
  }
}

function executeScript(event) {
  executesScript(event);
}
"""
        t['parameters']['script']['value']['stringValue'] = script_6

with open('drive_claims_integration.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print('drive_claims_integration.json updated successfully.')
