import requests
from xml.etree import cElementTree

sig = ''
url = 'http://api.lardi-trans.com/api/?method='
applications = []
id_for_update = []
response = requests.get(url + 'auth&login=armetprom&password=stal1701')
root = cElementTree.fromstring(response.content)
for child in root.iter('sig'):
    sig = child.text
response = requests.get(url + 'my.gruz.list&sig=' + sig)
root = cElementTree.fromstring(response.content)
for child in root.iter('id'):
    id_for_update.append(child.text)
    print(child.text)
for id_up in id_for_update:
    requests.post(url + "my.gruz.refresh&sig=" + sig + "&id=" + id_up)
    requests.post(url + "my.trans.refresh&sig=" + sig + "&id=" + id_up)
