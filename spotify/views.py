from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

import base64
import datetime
import json
import math
import requests
import secrets
import string
from dateutil import parser
from time import sleep
from urllib.parse import urlencode

from .forms import BpmPlaylistForm
from .models import BpmPlaylist, SpotifyUser
from .utils import *


"""
Authenticate/authorize Spotify account
"""
@login_required()
def spotifylogin(request):
    # check if still within rate limits
    retry = retry_time_left()
    if retry['time']:
        messages.error(request, retry['msg'])
        return redirect('/')

    # Check if user has spotify account linked
    if request.user.spotifyuser.spotify_user_id != '':
        # Check if access token is still valid
        if request.user.spotifyuser.access_token != '':
            print("\nCheck if access token is still valid\n")
            header = {
                'Authorization': 'Bearer ' + request.user.spotifyuser.access_token,
                'Content-Type': 'application/json'
            }
            try:
                res = requests.get('https://api.spotify.com/v1/me', headers=header)
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                return spotify_status_code_handler(request, res, err)
            except requests.exceptions.RequestException as err:
                return redirect('/')
            # access token is valid
            else:
                return redirect('/')

        # Try to get access token using refresh token, if it exists
        if request.user.spotifyuser.refresh_token != '':
            print("\nTry to get access token using refresh token\n")
            auth_options = {
                'grant_type': 'refresh_token',
                'refresh_token': request.user.spotifyuser.refresh_token
            }
            header = {
                'Authorization': 'Basic ' + base64.b64encode((settings.SPOTIFY_APP_ID + ':' + settings.SPOTIFY_APP_SECRET).encode("ascii")).decode("ascii"),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            try:
                res = requests.post('https://accounts.spotify.com/api/token', data=auth_options, headers=header)
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                if res.status_code != 429:
                    request.user.spotifyuser.refresh_token = ''
                    request.user.spotifyuser.save()
                
                return spotify_status_code_handler(request, res, err)
            except requests.exceptions.RequestException as err:
                return redirect('/')
            # used refresh token to successfully get access token
            else:
                res_json = res.json()

                request.user.spotifyuser.access_token = res_json['access_token']
                request.user.spotifyuser.expiration_datetime = timezone.now() + datetime.timedelta(seconds=res_json['expires_in'])
                request.user.spotifyuser.save()
                
                return redirect('/')
    
    # Request authorization from Spotify API
    print('\nRequest authorization from Spotify API\n')
    settings.SPOTIFY_STATE =  ''.join(secrets.choice(string.ascii_letters + string.digits) for x in range(16))

    req_params = {
        'response_type': 'code',
        'client_id': settings.SPOTIFY_APP_ID,
        'scope': settings.SPOTIFY_SCOPE,
        'redirect_uri': settings.SPOTIFY_REDIRECT_URL,
        'state': settings.SPOTIFY_STATE,
        'show_dialog': True
    }
    return redirect('https://accounts.spotify.com/authorize?' + urlencode(req_params))    


"""
Redirection URI from authenticating Spotify account in the Spotify API server
Registered with Spotify as the callback url
Provides an authorization code. Use to get access token and other auth details.
"""
@login_required
def gettoken(request):
    # Check if still within rate limits
    retry = retry_time_left()
    if retry['time']:
        messages.error(request, retry['msg'])
        return redirect('/')

    # Check state
    if settings.SPOTIFY_STATE == request.GET.get('state'):
        print('\nCheck state\n')
        # check if authorization failed (error or user didn't accept authorization request)
        # if there is an error, the error query will exist
        # TO DO log this error
        e = request.GET.get('error', '')
        print(f"\nError from Spotify authorization: {e}\n")
        if e != '':
            messages.error(request, "bpm wasn't authorized to access your Spotify account details.")
            raise PermissionDenied
        
        # Request access token from Spotify API       
        auth_options = {
            'code': request.GET.get("code"),
            'redirect_uri': settings.SPOTIFY_REDIRECT_URL, # used for validation only (there is no actual redirection)
            'grant_type': 'authorization_code'
        }
        auth_header = {
            'Authorization': 'Basic ' + base64.b64encode((settings.SPOTIFY_APP_ID + ':' + settings.SPOTIFY_APP_SECRET).encode("ascii")).decode("ascii"),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            res_auth = requests.post('https://accounts.spotify.com/api/token', data=auth_options, headers=auth_header)
            res_auth.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return spotify_status_code_handler(request, res_auth, err)
        except requests.exceptions.RequestException as err:
            return redirect('/')
        # Successfully received access token and other auth details
        else:
            res_auth_json = res_auth.json()

        # Get spotify account info (spotify_user_id, spotify_display_name)
        header = {
            'Authorization': 'Bearer ' + res_auth_json['access_token'],
            'Content-Type': 'application/json'
        }
        try:
            res_acct = requests.get('https://api.spotify.com/v1/me', headers=header)
            res_acct.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return spotify_status_code_handler(request, res_acct, err)
        except requests.exceptions.RequestException as err:
            return redirect('/')
        # Successfully received spotify account info
        else:
            res_acct_json = res_acct.json()

            # Spotifyuser already exists in the database
            if SpotifyUser.objects.filter(spotify_user_id__exact = res_acct_json['id']).exists() and res_acct_json['id'] != request.user.spotifyuser.spotify_user_id:
                messages.error(request, "This Spotify account is already linked to another bpm account. Try again after unlinking the bpm app from your Spotify account.")
                return redirect('/')
            
            # Update database with user's spotify account info
            request.user.spotifyuser.spotify_user_id = res_acct_json['id']
            request.user.spotifyuser.spotify_display_name = res_acct_json['display_name']
            request.user.spotifyuser.access_token = res_auth_json['access_token']
            request.user.spotifyuser.refresh_token = res_auth_json['refresh_token']
            request.user.spotifyuser.expiration = timezone.now() + datetime.timedelta(seconds=res_auth_json['expires_in'])
            request.user.spotifyuser.scope = settings.SPOTIFY_SCOPE
            request.user.spotifyuser.date_auth = timezone.now()
            request.user.spotifyuser.save()
            
            messages.success(request, "Successfully linked to your Spotify account!")
    
    print('\nredirecting\n')
    return redirect('/')

"""
Create a new bpm playlist
Generates a form to create a playlist and processes the form submitted by the user
"""
@login_required
def createplaylist(request):
    # Check if still within rate limits
    retry = retry_time_left()
    if retry['time']:
        messages.error(request, retry['msg'])
        return redirect('/')

    # Check if user signed into spotify account and if access_token exists
    if request.user.spotifyuser.spotify_user_id == '' or request.user.spotifyuser.access_token == '':
        return redirect('/spotifylogin')

    # POST request - process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = BpmPlaylistForm(request.POST)
        # check whether the form is valid:
        if form.is_valid():
            # check that bpm start <= bpm end
            if form.cleaned_data['bpm_start'] <= form.cleaned_data['bpm_end']:
                # Header for Spotify API calls
                header = {
                    'Authorization': 'Bearer ' + request.user.spotifyuser.access_token,
                    'Content-Type': 'application/json'
                }
                
                # Get Liked Songs
                liked_songs = []
                url_songs = 'https://api.spotify.com/v1/me/tracks?limit=50'
                while True:
                    try:
                        res = requests.get(url_songs, headers=header)
                        res.raise_for_status()
                    except requests.exceptions.HTTPError as err:
                        return spotify_status_code_handler(request, res, err)
                    except requests.exceptions.RequestException as err:
                        return redirect('/')
                    # Successfully received Liked Songs
                    else:
                        res_json = res.json()
                        for track in res_json['items']:
                            liked_songs.append(track['track']['id'])
                        
                        # Stop loop after the last set of Liked Songs
                        if res_json['next'] == None:
                            break

                        # update url to next api call
                        url_songs = res_json['next']
                        sleep(0.5)

                # Filter for songs within bpm range
                tracks_within_bpm = {}
                for i in range(0, len(liked_songs), 100):
                    param = {
                        'ids': ','.join(liked_songs[i:i+100])
                    }
                    try:
                        res = requests.get('https://api.spotify.com/v1/audio-features', params=param, headers=header)
                        res.raise_for_status()                    
                    except requests.exceptions.HTTPError as err:
                        return spotify_status_code_handler(request, res, err)
                    except requests.exceptions.RequestException as err:
                        return redirect('/')
                    # Received song features
                    else:
                        res_json = res.json()
                        for track in res_json['audio_features']:
                            bpm_nominal = track['tempo']

                            # tracks in bpm range
                            if form.cleaned_data['bpm_start'] <= bpm_nominal <= form.cleaned_data['bpm_end']:
                                if bpm_nominal in tracks_within_bpm:
                                    tracks_within_bpm[bpm_nominal].append(track['uri'])
                                else:
                                    tracks_within_bpm[bpm_nominal] = [track['uri']]
                            
                            # check for multiple of bpm that is within the bpm range
                            if form.cleaned_data['multiples_bpm']:
                                multiples = [2,4,8]
                                for multi in multiples:
                                    bpm_real = math.floor((bpm_nominal/multi)*(10**3))/(10**3)
                                    if form.cleaned_data['bpm_start'] <= bpm_real <= form.cleaned_data['bpm_end']:
                                        if bpm_real in tracks_within_bpm:
                                            tracks_within_bpm[bpm_real].append(track['uri'])
                                        else:
                                            tracks_within_bpm[bpm_real] = [track['uri']]
                                        break

                        sleep(0.5)
                
                # End process if new liked songs don't fall within bpm range
                if len(tracks_within_bpm) == 0:
                    messages.info(request, "None of the songs in Liked Songs fall within the playlist's bpm range.")
                    return redirect('/')    

                # # Set playlist name
                # # Move this to bpmplaylist model as default or initial value
                # if playlist_name:
                #     if form.cleaned_data['bpm_start'] == form.cleaned_data['bpm_end']:
                #         playlist_name = f"bpm Playlist - {form.cleaned_data['bpm_start']}"
                #     else:
                #         playlist_name = f"bpm Playlist - {form.cleaned_data['bpm_start']}-{form.cleaned_data['bpm_end']}"

                # Create playlist in Spotify
                playlist_id = None
                data = {
                    'name': form.cleaned_data['name'],
                    'description': f"bpm Playlist. bpm_start = {form.cleaned_data['bpm_start']}. bpm_end = {form.cleaned_data['bpm_end']}. multiples = {form.cleaned_data['multiples_bpm']}." 
                }
                try:
                    res = requests.post(f'https://api.spotify.com/v1/users/{request.user.spotifyuser.spotify_user_id}/playlists', data=json.dumps(data), headers=header)
                    res.raise_for_status()
                except requests.exceptions.HTTPError as err:
                    return spotify_status_code_handler(request, res, err)
                except requests.exceptions.RequestException as err:
                    return redirect('/')
                # Successfully created playlist
                else:
                    res_json = res.json()
                    playlist_id = res_json['id']

                    # Update database
                    playlist = BpmPlaylist(spotify_user=request.user.spotifyuser, playlist_id=res_json['id'], created_datetime=timezone.now(), last_update_datetime=timezone.now())
                    form_complete = BpmPlaylistForm(request.POST, instance=playlist)
                    form_complete.save()

                # Create an array of track uris in increasing bpm order
                tracks_within_bpm_sorted_uris = []
                for tempo in sorted(tracks_within_bpm):
                    tracks_within_bpm_sorted_uris += tracks_within_bpm[tempo]

                # Populate bpm playlist with filtered liked songs
                for uri_idx in range(0, len(tracks_within_bpm_sorted_uris), 100):
                    data = {
                        'uris': tracks_within_bpm_sorted_uris[uri_idx:uri_idx+100]
                    }
                    try:
                        res = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', data=json.dumps(data), headers=header)
                        res.raise_for_status()
                    except requests.exceptions.HTTPError as err:
                        return spotify_status_code_handler(request, res, err)
                    except requests.exceptions.RequestException as err:
                        return redirect('/')
                    # Successfully added batch of filtered liked songs
                    else:
                        sleep(0.5)
                
                messages.success(request, f"Playlist {form.cleaned_data['name']} was successfully created!")
                return redirect('/')

            messages.error(request, "The start of the bpm range should be less than or equal to the start.")

    # other methods - create a blank form
    else:
        form = BpmPlaylistForm()

    return render(request, 'playlist/create.html', {'form': form})

"""
Update playlist with tracks liked since creation or last update, if any 
"""
@login_required
def updateplaylist(request, playlist_id=None):
    # Check if still within rate limits
    retry = retry_time_left()
    if retry['time']:
        messages.error(request, retry['msg'])
        return redirect('/')

    # Check if user signed into spotify account and if access_token exists
    if request.user.spotifyuser.spotify_user_id == '' or request.user.spotifyuser.access_token == '':
        return redirect('/spotifylogin')

    # Identify playlist in database
    playlist = get_object_or_404(BpmPlaylist, playlist_id=playlist_id)

    # Header for Spotify API calls
    header = {
        'Authorization': 'Bearer ' + request.user.spotifyuser.access_token,
        'Content-Type': 'application/json'
    }
    
    # Get new additions to Liked Songs
    liked_songs_new = []
    url_songs = 'https://api.spotify.com/v1/me/tracks?limit=50'
    while True:
        try:
            res = requests.get(url_songs, headers=header)
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return spotify_status_code_handler(request, res, err)
        except requests.exceptions.RequestException as err:
            return redirect('/')
        # Successfully received batch of Liked Songs
        else:
            res_json = res.json()
            # Identify tracks added to Liked Songs after last update of the playlist
            for track in res_json['items']:
                tracked_liked_datetime = parser.parse(track['added_at'])
                if tracked_liked_datetime > playlist.last_update_datetime:
                    liked_songs_new.append(track['track']['id'])
            
            # Stop loop after the last set of Liked Songs
            if res_json['next'] == None:
                break

            # Update url to next api call
            url_songs = res_json['next']
            sleep(0.5)

    # End process if no new liked songs
    if len(liked_songs_new) == 0:
        messages.info(request, 'No new songs were added to Liked Songs since the playlist was last updated.')
        return redirect('/')

    # Get existing tracks in playlist
    existing_tracks = []
    existing_tracks_uri = []
    url_songs = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?limit=50'
    while True:
        try:
            res = requests.get(url_songs, headers=header)
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            return spotify_status_code_handler(request, res, err)
        except requests.exceptions.RequestException as err:
            return redirect('/')
        # Successfully received batch of tracks in playlist
        else:
            res_json = res.json()
            for track in res_json['items']:
                existing_tracks.append(track['track']['id'])
                existing_tracks_uri.append(track['track']['uri'])
            
            # Stop loop after the last set of Liked Songs
            if res_json['next'] == None:
                break

            # Update url to next api call
            url_songs = res_json['next']
            sleep(0.5)

    # Function to get tracks' bpm and store in dictionary
    tracks_within_bpm = {}
    def getbpm(tracks, existing):
        for i in range(0, len(tracks), 100):
            param = {
                'ids': ','.join(tracks[i:i+100])
            }
            try:
                res = requests.get('https://api.spotify.com/v1/audio-features', params=param, headers=header)
                res.raise_for_status()                    
            except requests.exceptions.HTTPError as err:
                return spotify_status_code_handler(request, res, err)
            except requests.exceptions.RequestException as err:
                return redirect('/')
            # Successfully received batch of track features
            else:
                res_json = res.json()
                for track in res_json['audio_features']:
                    bpm_nominal = track['tempo']

                    if existing:
                        if bpm_nominal in tracks_within_bpm:
                            tracks_within_bpm[bpm_nominal].append((track['uri'],existing))
                        else:
                            tracks_within_bpm[bpm_nominal] = [(track['uri'],existing)]
                    else:
                        # Tracks in bpm range
                        if playlist.bpm_start <= bpm_nominal <= playlist.bpm_end:
                            if bpm_nominal in tracks_within_bpm:
                                tracks_within_bpm[bpm_nominal].append((track['uri'],existing))
                            else:
                                tracks_within_bpm[bpm_nominal] = [(track['uri'],existing)]
                        
                        # Check for multiple of bpm that is within the bpm range
                        if playlist.multiples_bpm:
                            multiples = [2,4,8]
                            for multi in multiples:
                                bpm_real = math.floor((bpm_nominal/multi)*(10**3))/(10**3)
                                if playlist.bpm_start <= bpm_real <= playlist.bpm_end:
                                    if bpm_real in tracks_within_bpm:
                                        tracks_within_bpm[bpm_real].append((track['uri'],existing))
                                    else:
                                        tracks_within_bpm[bpm_real] = [(track['uri'],existing)]
                                    break

                sleep(0.5)
    
    # Filter for the new tracks that fall within the bpm range
    getbpm(liked_songs_new, False)
    
    # End process if new liked songs don't fall within bpm range
    if len(tracks_within_bpm) == 0:
        messages.info(request, "None of the new songs in Liked Songs fall within the playlist's bpm range.")
        return redirect('/')
    
    # Collect the bpm of the existing tracks
    getbpm(existing_tracks, True)

    # Create an array of track uris in increasing bpm order
    tracks_within_bpm_sorted_uris = []
    for tempo in sorted(tracks_within_bpm):
        tracks_within_bpm_sorted_uris += tracks_within_bpm[tempo]
    
    # Create an array of tracks not in the playlist
    tracks_not_existing_uris = {}
    pointer_start = -2
    pointer_end = -2
    for idx, track in enumerate(tracks_within_bpm_sorted_uris):
        if not track[1]:
            if pointer_end == idx - 1:
                tracks_not_existing_uris[pointer_start].append(track[0])
            else:
                tracks_not_existing_uris[idx] = [track[0]]
                pointer_start = idx
            pointer_end = idx

    # Add non existing tracks to bpm playlist in bpm order
    for position in tracks_not_existing_uris:
        for uri_idx in range(0, len(tracks_not_existing_uris[position]), 100):
            data = {
                'position': position,
                'uris': tracks_not_existing_uris[position][uri_idx:uri_idx+100]
            }
            try:
                res = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', data=json.dumps(data), headers=header)
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                return spotify_status_code_handler(request, res, err)
            except requests.exceptions.RequestException as err:
                return redirect('/')
            # Successfully added batch of tracks
            else:
                sleep(0.5)

    # Record update datetime in database
    playlist.last_update_datetime = timezone.now()
    playlist.save()

    # Success message
    if len(tracks_not_existing_uris):
        messages.success(request, f"Your playlist {playlist.name} was updated with {len(tracks_not_existing_uris)} of the latest additions to your Liked Songs!")
    else:
        messages.success(request, f"The latest additions to your Liked Songs did not fall in the bpm range of your playlist {playlist.name}.")
    
    return redirect('/')

@login_required
def deleteplaylist(request, playlist_id=None):
    # Check if still within rate limits
    retry = retry_time_left()
    if retry['time']:
        messages.error(request, retry['msg'])
        return redirect('/')

    # Check if user signed into spotify account and if access_token exists
    if request.user.spotifyuser.spotify_user_id == '' or request.user.spotifyuser.access_token == '':
        return redirect('/spotifylogin')

    # Identify playlist in database
    playlist = get_object_or_404(BpmPlaylist, playlist_id=playlist_id)

    # Delete from spotify if it exists
    # Note: in spotify, no concept of deleting playlists. Instead, "unfollow" playlists
    header = {
        'Authorization': 'Bearer ' + request.user.spotifyuser.access_token,
        'Content-Type': 'application/json'
    }
    try:
        res = requests.delete(f'https://api.spotify.com/v1/playlists/{playlist_id}/followers', headers=header)
        res.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return spotify_status_code_handler(request, res, err)
    except requests.exceptions.RequestException as err:
        return redirect('/')
    # Successfully delete playlist from Spotify
    else:
        # Delete playlist from database
        playlist.delete()           
        messages.success(request, f'Playlist {playlist.name} was successfully deleted!')
        return redirect('/')
