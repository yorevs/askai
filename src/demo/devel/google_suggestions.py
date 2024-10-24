import json
import requests

if __name__ == '__main__':
    query = 'home'

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
    }

    response = requests.get(f"http://google.com/complete/search?client=chrome&q={query}")

    for completion in json.loads(response.text)[1]:
        print(completion)

