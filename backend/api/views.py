from django.shortcuts import render
from django.http import HttpResponse
import json
import pymongo

def bodyToJson(reqBody):
  bodyJson = {}
  for param in reqBody.split('&'):
    keyVal = param.split('=')
    bodyJson[keyVal[0]] = keyVal[1]
  return bodyJson

def signup(request):
  req_body = request.body.decode('utf-8')
  userJson = bodyToJson(req_body)

  myclient = pymongo.MongoClient("mongodb://localhost:27017/")
  mydb = myclient['moviedb']
  usersCol = mydb['users']

  usersCol.insert_one(userJson)

  return HttpResponse("Hello world")