from django.shortcuts import render
from django.http import HttpResponse
import json
import pymongo
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

from bs4 import BeautifulSoup
import urllib.request as urllib

import os.path
BASE = os.path.dirname(os.path.abspath(__file__))

def bodyToJson(reqBody):
  bodyJson = {}
  for param in reqBody.split('&'):
    keyVal = param.split('=')
    bodyJson[keyVal[0]] = keyVal[1]
  return bodyJson

def signup(request):
  req_body = request.body.decode('utf-8')
  userJson = bodyToJson(req_body)

  myclient = pymongo.MongoClient('mongodb://localhost:27017/')
  mydb = myclient['moviedb']
  usersCol = mydb['users']

  if not usersCol.count({ '$or': [{'username': userJson['username']}, {'email': userJson['email']}]}) == 0:
    print('Already exist')
    myclient.close()
    resJson = json.dumps({'msg': 'Username or email already taken'}, indent = 4)
    return HttpResponse(resJson, content_type="application/json", status=409)
  else:
    newUser = usersCol.insert(userJson)
    myclient.close()
    resJson = json.dumps({'msg': 'Sign Up Succesful', 'id': str(newUser[0]['_id'])}, indent = 4)
    response = HttpResponse(resJson, content_type="application/json", status=200)
    response.set_cookie('id', str(newUser))
    return response


def login(request):
  req_body = request.body.decode('utf-8')
  userJson = bodyToJson(req_body)
  myclient = pymongo.MongoClient('mongodb://localhost:27017/')
  mydb = myclient['moviedb']
  usersCol = mydb['users']
  cursor = list(usersCol.find({ '$and': [{'username': userJson['username']}, {'password': userJson['password']}]}, {'_id':1}))
  if not cursor:
    resJson = json.dumps({'msg': 'Invalid username or password'}, indent = 4)
    return HttpResponse(resJson, content_type="application/json", status=401)
  else:
    resJson = json.dumps({'msg': 'Login Successful', 'id': str(cursor[0]['_id'])})
    response = HttpResponse(resJson, content_type="application/json", status=200)
    response.set_cookie('id', str(cursor[0]['_id'])) 
    return response


def searchByTitle(request):
  myclient = pymongo.MongoClient('mongodb://localhost:27017/')
  mydb = myclient['moviedb']
  moviesCol = mydb['movies']
  title = request.GET['title']
  cursor = moviesCol.find({'title' : {'$regex' : title, '$options' : 'i'}}, {'_id': 1, 'title': 1}).sort([('imdb', -1)]).limit(5)
  myclient.close()
    
  if cursor:
    asJson = json.dumps(list(cursor))
    return HttpResponse(asJson, content_type='application/json', status=200)

      
def getRecommendationsByUserLikes(request):
  ttid = request.GET['movieid']
  responseList = []
  for movieid in get_movie_recommendation(ttid):
    responseList.append({'movieid': movieid, 'posterurl': getImgUrl(movieid)})

  asJson = json.dumps(responseList)
  return HttpResponse(asJson, content_type='application/json', status=200)

def getImgUrl(ttid):


  ttid = "tt" + str(ttid).zfill(7)
  url = 'https://www.imdb.com/title/' + ttid
  imdburl = urllib.urlopen(url)
  soup = BeautifulSoup(imdburl, features='html.parser')
  li = soup.find('div', {'class': 'poster'})
  childImg = li.findChild('img')
  return (childImg['src'].split('V1_')[0] + 'V1_.jpg')



def get_movie_recommendation(movieId):
  movieId = (int(movieId))
  movies = pd.read_csv(os.path.join(BASE, "moviesFinal.csv"))
  ratings = pd.read_csv(os.path.join(BASE, "ratingsUp.csv"))

  final_dataset = ratings.pivot(index='movieId',columns='userId',values='rating')
  final_dataset.fillna(0,inplace=True)
  csr_data = csr_matrix(final_dataset.values)
  final_dataset.reset_index(inplace=True)

  knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
  knn.fit(csr_data)

  n_movies_to_reccomend = 5    
      
  movie_idx = final_dataset[final_dataset['movieId'] == movieId].index[0]
  distances , indices = knn.kneighbors(csr_data[movie_idx],n_neighbors=n_movies_to_reccomend+1)    
  rec_movie_indices = sorted(list(zip(indices.squeeze().tolist(),distances.squeeze().tolist())),key=lambda x: x[1])[:0:-1]
  recommend_frame = []
    
  for index, val in rec_movie_indices:
    movie_id = final_dataset.iloc[index]['movieId']
    recommend_frame.append(int(movie_id))
  return recommend_frame