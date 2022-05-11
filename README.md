# bpm

## Overview
Everyone has different ways of organizing their music on Spotify. Some enjoy building out intensive playlists for all possible occasions (rainy days, anyone?) and others like the quick and simple method of pressing on the heart and having all of their liked songs in one place. Most of us probably do a combination of the two, and there's a reason why. Playlists tend to get outdated and require some effor to stay relevant both in your forever evolving music taste and the original purpose of the playlist. In contrast, liked songs tend to stay fresh because it's easy to like and unlike songs (with the press of a button!), but it can become a behemoth and be unfocused. 

This negative correlation between focus and freshness is fundamentally at issue when creating exercise playlists. For some people, music is the fuel for a good  workout, and the worst thing that can happen is to hear Lee Sun Hee's ["Fox Rain"](https://open.spotify.com/track/5YyJ419QcZb49wjO3Dy920?si=53bc1fd2598b4927) after running in step to AUDREY NUNA's ["Comics Sans"](https://open.spotify.com/track/2dQn5I17lUiQ8ZpjqMh3TU?si=9a60d68e2360425c). (Note: They're both amazing; you should check them out.) Sure, we can make exercise playlists or listen to the countless pre-made ones already available, but the same songs and the same progression can get boring and making/maintaining them takes too much time and effort for the busy modern-day human.

Then, [here comes the boy](https://www.tiktok.com/@june_banoon/video/6979637268126420230) -- I mean, bpm. bpm generates playlists from tracks in the user's Liked Songs (aka Your Songs) that are within the bpm range of choice -- and in bpm order at that! The user can also update the playlists with the newest additions to Liked Songs (as long as the tracks are within the bpm range set for that playlist). I also took into account situations where a song's bpm may fall outside of the range but is a multiple of a bpm within the range (see the 'Multiples' section below). 

The Django framework was used to create this app.

There were a few challenges with this app:
1. Keeping in sync the app's database and Spotify's database on bpm playlists
2. Handling the rate limit on calls to the Spotify API

bpm can be used for much more than just exercise (e.g. lullaby, study, etc.); it's just a matter of finding the appropriate and desired bpm range. 


## Understanding the App Features
### Multiples
You can either select or unselect Multiples when creating a bpm playlist. Selecting it means that tracks whose tempos are multiples of a bpm in the bpm range will also be included in the playlist. It may make sense to select it for a running playlist (It might not matter if a song is at bpm 120 or 240 as long as your feet are hitting the pavement at the same rate), but less so for a sleeping playlist (You definitely want to hear a song 50 bpm and not 200). Note that if selected, only tracks with higher bpms, not lower, will be considered.

### Updates
A goal of this app is to keep freshness alive and give deferrence to the natural evolution of a person's musical taste. To do so, new additions to Liked Songs are added to existing playlists via the Udpate functionality. The app will consider the new additions to see if they are within the selected playlist's bpm range, and if so, add them to the playlist (in bpm order!)


## To Use the App
The deployment is still in progress. Once deployed, I'll post the link here. For now, you'll have to do the following:

First, you need to register as a Developer on [Spotify for Developers site](https://developer.spotify.com/). Then, go to your [Dashboard](https://developer.spotify.com/dashboard/applications) to create an app and get a Client ID and Client Secret. Also, while you're there, change the redirect URI to http://127.0.0.1:8000/gettoken (replace the domain name with the one that you're using). Take the Client ID and Client Secret and add to a .env file in your root project folder.

You're also going to need to set up a database. I used MySQL. Replace the details of the DATABASE variable in settings.py with your database info. Follow the [Djano tutorial on database setup](https://docs.djangoproject.com/en/4.0/intro/tutorial02/) if you need help.


## Upcoming features
* Expand source from Liked Songs to any other playlsit
* Limit playlists by time
* Expand dashboard to display graphs/charts of playlist compositions
* Collecting steps per minute via phone or Fitbit