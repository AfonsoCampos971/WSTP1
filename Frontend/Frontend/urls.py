"""
URL configuration for Frontend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from PicthStats import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('genres/', views.genre_list, name='genres'),
    path('artists/<str:pk>/', views.artist_detail, name='artist_detail'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/create/', views.create_review, name='create_review'),
    path('reviews/<str:pk>/', views.review_detail, name='review_detail'),
    path('authors/<str:pk>/', views.author_detail, name='author_detail'),
    path('labels/<str:pk>/', views.label_detail, name='label_detail'),

]
