from django.shortcuts import render
from django.http import HttpResponse
import json
import pymongo
from bson.objectid import ObjectId

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import random

from bs4 import BeautifulSoup
import urllib.request as urllib

import os.path
BASE = os.path.dirname(os.path.abspath(__file__))

# POST
def signup(request):
    req_body = request.body.decode('utf-8')
    userJson = bodyToJson(req_body)

    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    usersCol = mydb['users']

    if not usersCol.count({'$or': [{'username': userJson['username']}, {'email': userJson['email']}]}) == 0:
        print('Already exist')
        myclient.close()
        resJson = json.dumps(
            {'msg': 'Username or email already taken'}, indent=4)
        return HttpResponse(resJson, content_type="application/json", status=409)
    else:
        newUser = usersCol.insert(userJson)
        myclient.close()
        resJson = json.dumps(
            {'msg': 'Sign Up Succesful', 'id': str(newUser[0]['_id'])}, indent=4)
        response = HttpResponse(
            resJson, content_type="application/json", status=200)
        return response

# POST
def login(request):
    req_body = request.body.decode('utf-8')
    userJson = bodyToJson(req_body)
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    usersCol = mydb['users']
    cursor = list(usersCol.find({'$and': [{'username': userJson['username']}, {
                  'password': userJson['password']}]}, {'_id': 1}))
    if not cursor:
        resJson = json.dumps({'msg': 'Invalid username or password'}, indent=4)
        return HttpResponse(resJson, content_type="application/json", status=401)
    else:
        resJson = json.dumps(
            {'msg': 'Login Successful', 'id': str(cursor[0]['_id'])})
        response = HttpResponse(
            resJson, content_type="application/json", status=200)
        return response

# GET
def searchByTitle(request):
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    moviesCol = mydb['movies']
    title = request.GET['title']
    cursor = moviesCol.find({'title': {'$regex': title, '$options': 'i'}}, {
                            '_id': 1, 'title': 1}).sort([('imdb', -1)]).limit(5)
    myclient.close()

    if cursor:
        asJson = json.dumps(list(cursor))
        return HttpResponse(asJson, content_type='application/json', status=200)

# GET
# get recommendations based on the other user likes
def getRecommendationsByUserLikes(request):
    ttid = int(request.GET['movieid'])
    responseList = []
    movies = pd.read_csv(os.path.join(BASE, "moviesFinal.csv"))

    for movieid in get_movie_recommendation(ttid, movies):
        url = movies[movies['imdb_title_id']== movieid]['poster_url'].values[0]
        responseList.append({'movieid': movieid, 'poster_url':url})

    asJson = json.dumps(responseList)
    return HttpResponse(asJson, content_type='application/json', status=200)


# POST
# star a movie and add it into starred movies field of user in database
# params: userid, movieid, star
def likeMovie(request):
    req_body = request.body.decode('utf-8')
    reqJson = bodyToJson(req_body)
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    usersCol = mydb['users']

    
    #usersCol.update(
    #    {'_id': ObjectId(reqJson['userid'])},
    #    {'$push': { 'starredMovies': {'movieid': int(reqJson['movieid']), 'star': int(reqJson['star'])}}})


    usersCol.update({'starredMovies':{
        '$not': {
            '$elemMatch': {
                'movieid': int(reqJson['movieid'])
            }
        }
    }}, {
        '$addToSet': {
            'starredMovies': {
                'movieid': int(reqJson['movieid']),
                'star': int(reqJson['star'])
            }
        }
    }, upsert=True)
    
    usersCol.update({'_id': ObjectId(reqJson['userid']), 'starredMovies.movieid': int(reqJson['movieid'])}, {'$set': {
        'starredMovies.$.star': int(reqJson['star'])
    }}, upsert=True)

    return HttpResponse(status=200)


# GET
def getLikedMovieRandom(request):
    userid = request.GET['userid']
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    usersCol = mydb['users']

    likedMovies = mydb['users'].find(
        {'_id': ObjectId(userid)}, 
        {'_id':0, 'starredMovies':1, 'starredMovies':{'$filter': { 'input': '$starredMovies', 'as': 'mov', 'cond': {'$gt': ['$$mov.star', 3]}}}})
    

    likedMovies = list(likedMovies[0]['starredMovies'])
    likedMovies = random.choice(likedMovies)
    asJson = json.dumps(likedMovies)
    return HttpResponse(asJson, content_type='application/json', status=200)



# GET
def getMovieDetails(request):
    ttid = request.GET['movieid']
    uid = request.GET['userid']
    
    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    
    starList = [1,2,3,4,5]

    movieCursor = mydb['movies'].find({'_id': int(ttid)})[0]
    #starCursor = mydb['users'].find(
    #    {'_id': ObjectId(uid)}, 
    #    {'_id':0, 'starredMovies':1, 'starredMovies':{'$elemMatch':{':$eq' {'movieid': int(ttid), 'star': 5}}}})
    

    starCursor = mydb['users'].find(
        {'_id': ObjectId(uid)}, 
        {'_id':0, 'starredMovies':1, 'starredMovies':{'$filter': { 'input': '$starredMovies', 'as': 'mov', 'cond': {'$eq': ['$$mov.movieid', int(ttid)]}}}})
    
    myclient.close()

    if not len(starCursor[0]['starredMovies']):
        movieCursor['star'] = 0
    else:
        movieCursor['star'] = starCursor[0]['starredMovies'][0]['star']
    
    asJson = json.dumps(movieCursor)
    return HttpResponse(asJson, content_type='application/json', status=200)

def getName(request):
    ttid = int(request.GET['movieid'])

    myclient = pymongo.MongoClient('mongodb://localhost:27017/')
    mydb = myclient['moviedb']
    moviesCol = mydb['movies']

    cursor = moviesCol.find({'_id': ttid},{'_id':0, 'title':1})
    myclient.close()

    if cursor:
        asJson = json.dumps(cursor[0])
        return HttpResponse(asJson, content_type='application/json', status=200)
    

def get_movie_recommendation(movieId, movies):
    movieId = (int(movieId))
    ratings = pd.read_csv(os.path.join(BASE, "ratingsUp.csv"))

    ratingsMatrix = ratings.pivot(
        index='movieId', columns='userId', values='rating')
    ratingsMatrix.fillna(0, inplace=True)
    csr_data = csr_matrix(ratingsMatrix.values)
    ratingsMatrix.reset_index(inplace=True)

    knn = NearestNeighbors(
        metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
    knn.fit(csr_data)

    n_movies_to_reccomend = 5    
      
    movie_idx = ratingsMatrix[ratingsMatrix['movieId'] == movieId].index[0]
        
    distances , indices = knn.kneighbors(csr_data[movie_idx],n_neighbors=n_movies_to_reccomend+1)
    
    rec_movie_indices = sorted(list(zip(indices.squeeze().tolist(),distances.squeeze().tolist())),key=lambda x: x[1])[:0:-1]
    
    recommend_frame = []
    for index, val in rec_movie_indices:
        movie_id = ratingsMatrix.iloc[index]['movieId']
        recommend_frame.append(int(movie_id))
        idx = movies[movies['imdb_title_id'] == movie_idx]
            
    return recommend_frame


def bodyToJson(reqBody):
    bodyJson = {}
    print('###########################################')
    for param in reqBody.split('&'):
        keyVal = param.split('=')
        print(keyVal)
        bodyJson[keyVal[0]] = keyVal[1]
    return bodyJson


def getDescriptionRecommendation(request):

    movieId = int(request.GET['movieid'])

    pd.read_csv(os.path.join(BASE, "ratingsUp.csv"))
    movies = pd.read_csv(os.path.join(BASE, "withPosterUrl.csv"))
    descriptionSimilarity = pd.read_csv(os.path.join(BASE, "descriptionSim.csv"))


    mov = descriptionSimilarity[descriptionSimilarity['imdb_title_id'] == int(movieId)]

    sim_scores = []
    for i in range(1,6):
        sim_scores.append(mov[str(i)].values)
    
    #idx = indices[movieId]
    #sim_scores = list(enumerate(cosine_sim[idx]))
    #sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[0:30]
    
    sim_scores = [i[0] for i in sim_scores]
    movie_ids = []
    for score in sim_scores:
        movie_ids.append(
            {
                'movieid': str(movies.iloc[int(float(score[1:-1].split(' ')[0]))]['imdb_title_id']),
                'poster_url': str(movies.iloc[int(float(score[1:-1].split(' ')[0]))]['poster_url'])
            })

    asJson = json.dumps(movie_ids)
    return HttpResponse(asJson, content_type='application/json', status=200)