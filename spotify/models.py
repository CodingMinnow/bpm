from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.utils import timezone

from annoying.fields import AutoOneToOneField
from zoneinfo import ZoneInfo
import datetime

# Spotify user ID (Ex.: wizzler) https://developer.spotify.com/documentation/web-api/#spotify-uris-and-ids
# spotify display name https://developer.spotify.com/documentation/web-api/reference/#/operations/get-current-users-profile
class SpotifyUser(models.Model):
    def __str__(self):
        return self.spotify_display_name
    
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = AutoOneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    spotify_user_id = models.CharField(max_length=50)
    spotify_display_name = models.CharField(max_length=191)
    access_token = models.CharField(max_length=300)
    refresh_token = models.CharField(max_length=300)
    expiration = models.DateTimeField(default=timezone.make_aware(datetime.datetime.min, ZoneInfo('UTC')))
    scope = models.CharField(max_length=191)
    date_auth = models.DateTimeField(default=timezone.make_aware(datetime.datetime.min, ZoneInfo('UTC')))

# Spotify ID for playlists (Ex.: 3cEYpjA9oz9GiPac4AsH4n) https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlist
class BpmPlaylist(models.Model):
    def __str__(self):
        return self.playlist_id
    
    spotify_user = models.ForeignKey(SpotifyUser, on_delete=models.PROTECT)
    playlist_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=50)
    created_datetime = models.DateTimeField(default=timezone.now)
    last_update_datetime = models.DateTimeField(default=timezone.now)
    bpm_start = models.PositiveSmallIntegerField()
    bpm_end = models.PositiveSmallIntegerField()
    multiples_bpm = models.BooleanField(default=True)

    # class Meta:
    #     constraints = [
    #         CheckConstraint(
    #             check=Q(bpm_start__lte=F('bpm_end')), 
    #             name='bpm_check'
    #         ) 
    #     ]
