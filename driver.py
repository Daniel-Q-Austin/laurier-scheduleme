import requests
import scheduleme


url = scheduleme.url_builder("EC121", "fall", "2021")
print(url)

webpage = requests.get(url)
#print(webpage.content)
#scheduleme.parse(url)