import requests
import scheduleme
import request_interception


url = scheduleme.url_builder("EC120", "fall", "2021")
print(request_interception.process_webpage(url))
#print(url)

webpage = requests.get(url)
#print(webpage.content)
#scheduleme.parse(url)