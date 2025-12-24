import requests
try:
    r = requests.get('http://localhost:5000/api/state')
    print(r.status_code)
    print(r.text)
except Exception as e:
    print(e)
