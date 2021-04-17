import requests

url = "https://movie-database-imdb-alternative.p.rapidapi.com/"

querystring = {"i":"tt4154796","r":"json"}

headers = {
    'x-rapidapi-key': "cdfd6ae0bamshab670431d96d5ffp19e3a4jsn0ace9484330a",
    'x-rapidapi-host': "movie-database-imdb-alternative.p.rapidapi.com"
    }

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)