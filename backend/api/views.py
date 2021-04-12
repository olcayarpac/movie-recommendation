from django.shortcuts import render
from django.http import HttpResponse
import json
import pymongo

# TODO: giriş yap ve kaydol fonksiyonlarını düzgünce geliştir
# TODO: kaydol fonksiyonu username ve email kontrolü yapacak
# TODO: kayıt olma veya giriş yapma başarılı olduğunda userid döndüreceğiz
# TODO: ilerleyen zamanlarda userid yerine token kontrolü yapılabilir

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
    return HttpResponse('Username or email already taken', status=409)
  else:
    newUser = usersCol.insert(userJson)
    myclient.close()
    response = HttpResponse("Sign Up Succesful", status=200)
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
    return HttpResponse('Invalid username or password', status=401)
  else:
    response = HttpResponse('Login Successful', status=200)
    response.set_cookie('id', str(cursor[0]['_id'])) 
    return response