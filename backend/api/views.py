from django.shortcuts import render
from django.http import HttpResponse
import json
import pymongo


# HQQ-SZAS2R-NETT27

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
    resJson = json.dumps({'msg': 'Sign Up Succesful', 'id': str(cursor[0]['_id'])}, indent = 4)
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
    return respons-
