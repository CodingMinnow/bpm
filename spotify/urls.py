from django.urls import include, path

from . import views

urlpatterns = [
    path('spotifylogin/', views.spotifylogin, name='spotifylogin'),
    path('gettoken/', views.gettoken, name='gettoken'),
    path('createplaylist/', views.createplaylist, name='createplaylist'),
    path('update/<playlist_id>', views.updateplaylist, name='updateplaylist'),
    path('delete/<playlist_id>', views.deleteplaylist, name='deleteplaylist'),
    # path('exceededrate/', views.exceededrate, name='exceededrate')
]
