from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone


import datetime
import json
# import requests
# from time import sleep
from zoneinfo import ZoneInfo

"""
Returns a dictionary with the time left until Spotify API can be called again and the corresponding message to display
"""
def retry_time_left():
    diff_sec = (settings.SPOTIFY_RETRY_AFTER_TIME - timezone.now()).total_seconds()
    if diff_sec > 0:
        return {'time': divmod(diff_sec, 60)[0], 'msg': f"Y'all showed us too much love, so Spotify told us to chill out. Try again in {divmod(diff_sec, 60)[0]} minutes."}

    return {'time': 0, 'msg': ''}

"""
Handles status code errors from Spotify API calls
Returns a HttpResponse type
"""
def spotify_status_code_handler(req, res, err):
    # Bad or expired token. Reset database and reauthenticate spotify user
    if res.status_code == 401:
        # reset access token and expiration
        req.user.spotifyuser.access_token = ''
        req.user.spotifyuser.expiration = timezone.make_aware(datetime.datetime.min, ZoneInfo('UTC'))
        req.user.spotifyuser.save()

        # save the current url to sessions
        req.session['expired_token_redirect_url'] = req.path

        return redirect('/spotifylogin')
    # Exceeded rate limit
    elif res.status_code == 429:
        settings.SPOTIFY_RETRY_AFTER_TIME = timezone.now() + datetime.timedelta(seconds=res.headers['Retry-After']) 
        messages.error(req, retry_time_left()['msg'])
        return redirect('/')
    # Some other status code
    else:
        print(json.loads(res.content.decode("utf-8")))
        messages.error(req, 'There has been an error.')
        return redirect('/')


"""
"""
# def getlikedsongs(request):
#     liked_songs = []
#     header_songs = {
#         'Authorization': 'Bearer ' + request.user.spotifyuser.access_token,
#         'Content-Type': 'application/json'
#     }
#     url_songs = 'https://api.spotify.com/v1/me/tracks?limit=50'
#     while True:
#         res_songs = requests.get(url_songs, headers=header_songs)

#         # TO DO status code handlers
#         # Success 200
#         if res_songs.status_code == 200:
#             res_songs_json = res_songs.json()
#             # print(res_songs_json['items'][0]['track']['id'])
#             for track in res_songs_json['items']:
#                 liked_songs.append(track['track']['id'])
            
#             # Stop loop after the last set of Liked Songs
#             if res_songs_json['next'] == None:
#                 break

#             # pause for a few seconds
#             sleep(0.5)

#             # update url to next api call
#             url_songs = res_songs_json['next']

#         # Bad or expired token. Reset database and reauthenticate spotify user
#         elif res_songs.status_code == 401:      
#             return redirect('/spotifylogin')
#         # Exceeded rate limit
#         elif res_songs.status_code == 429:   
#             # update SPOTIFY_RETRY_AFTER_TIME in settings
#             settings.SPOTIFY_RETRY_AFTER_TIME = timezone.now() + datetime.timedelta(seconds=res_songs.headers['Retry-After']) 

#             return render(request, 'rate_exceeded.html', {'retry_time': divmod(res_songs.headers['Retry-After'],60)[0]})
#         else:
#             print(json.loads(res_songs.content.decode("utf-8"))['error']['message'])
#             return redirect('/')
    
#     return liked_songs