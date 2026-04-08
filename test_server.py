import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
url = 'https://149.154.166.110/botREDACTED_TOKEN/getMe'
req = urllib.request.Request(url, headers={'Host': 'api.telegram.org'})
r = urllib.request.urlopen(req, context=ctx, timeout=10)
print(r.read().decode())
