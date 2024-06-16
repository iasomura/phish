from requests_oauthlib import OAuth1Session as session

URL = "https://api.twitter.com/2/tweets/NaomiSuzuki_"

#各種キーとトークは各自で置き換える
CK= 'rrnY1WHOOFRdDfKkCyNTju2wJ'
CS= 'PByxtCR9SIDYCVVTfw8fCS3NOSm3HEhOQ5xtxDCRy0n7pQg9CA'
AT= '1346756863862349826-8Db7AmK4p0EkE6VlaL3c5Jd4ABRHwI'
ATS= 'kO9od6AutTaEqbVB6YOcWDIyvrQUPrz1WBs3761Oh7yJs'


req = session(CK, CS, AT, ATS)

response = req.get(URL)
print(response.text)
