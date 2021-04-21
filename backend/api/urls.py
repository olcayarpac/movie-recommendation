from django.urls import path

from . import views

urlpatterns = [
    path('signup', views.signup, name='singup'),
    path('login', views.login, name='login'),
    path('searchTitle', views.searchByTitle, name='searchTitle'),
    path('getRecommendationsByUserLikes', views.getRecommendationsByUserLikes, name='getRecommendationsByUserLikes')
]