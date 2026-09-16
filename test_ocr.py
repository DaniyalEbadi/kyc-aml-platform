import requests, time, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

login = requests.post('http://localhost:8002/api/v1/auth/login', json={'email':'admin@parsheid.ir','password':'admin123'})
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Create app
a = requests.post('http://localhost:8002/api/v1/applications', headers=headers, json={}).json()
app_id = a['id']
print('App:', app_id, a['application_number'])

# Upload test image - use correct content_type
with open('F:/kyc-aml-platform/test_national_card.jpg', 'rb') as f:
    files = {'file': ('test_national_card.jpg', f, 'image/jpeg')}
    data = {'app_id': app_id, 'doc_type': 'national_id'}
    r = requests.post('http://localhost:8002/api/v1/documents/upload', headers=headers, files=files, data=data)

print('Upload:', r.status_code)
resp = r.json()

if r.status_code != 200:
    print('Error:', resp)
    sys.exit(1)

doc_id = resp['document']['id']
job_id = resp['job']['id']
print('Doc:', doc_id)
print('Job:', job_id, '-', resp['job']['status'])

# Wait for OCR processing (easyocr first run downloads models)
print('Waiting for OCR processing...')
time.sleep(10)

# Check job status
job = requests.get(f'http://localhost:8002/api/v1/jobs/{job_id}', headers=headers).json()
print('\nJob:', job['status'], '-', job.get('stage', ''), '-', job.get('progress', 0), '%')

# Get document with extracted fields
doc = requests.get(f'http://localhost:8002/api/v1/documents/{doc_id}', headers=headers).json()
print('\n=== Extracted Fields ===')
for f in doc.get('fields', []):
    print(f'  {f["field_label"]}: {f["value"]} ({f["confidence"]:.0%})')

# Get verifications
detail = requests.get(f'http://localhost:8002/api/v1/applications/{app_id}', headers=headers).json()
print('\n=== Verifications ===')
for v in detail.get('verifications', []):
    print(f'  {v["kind"]}: status={v["status"]}, score={v["score"]}')
    if v.get('details'):
        print(f'    provider={v["details"].get("provider")}, simulated={v["details"].get("is_simulated")}')
