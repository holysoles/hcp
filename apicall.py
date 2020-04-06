import requests


def verify(key):
    # r = requests.put('https://api.du-pl.com/hcp/verify', data={'key': key})
    # body = r.json()
    # isverified = body['verified'] == "True"
    isverified = True

    if isverified:
        return True
    else:
        return False
