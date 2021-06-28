import requests
import scheduleme
import request_interception


url = scheduleme.url_builder("EC120", "fall", "2021")
data = request_interception.intercept_request(url)
scheduleme.parse(data)
#print(url)

#webpage = requests.get(url)
#print(webpage.content)
#scheduleme.parse(url)