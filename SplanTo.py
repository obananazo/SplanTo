#- Author: Walter Kopp
# April 2021

import datetime
from logging import raiseExceptions
import logging
import spotipy
import os

from spotipy.oauth2 import SpotifyOAuth

BASE_URL = 'https://api.spotify.com/v1' # base URL of all Spotify API endpoints

CLIENT_ID = os.environ['SPLANTO_CLIENT_ID']
CLIENT_SECRET = os.environ['SPLANTO_CLIENT_SECRET']


def main():
    
    banner()
    
    sp = auth_manager()
    
    playlist_id = get_playlist_id(sp, description='Plan to hear')

    track_list = get_playlist_tracks(sp, playlist_id)
    
    tracks = filter_old_tracks(track_list)
    
    delete_tracks(sp, playlist_id, tracks)


def banner():
    
    print(
        '  _________      .__                 __           \n'
        ' /   _____/_____ |  | _____    _____/  |_  ____  \n'
        ' \_____  \\\\____ \|  | \__  \  /    \   __\/  _ \\\n'
        ' /        \  |_> >  |__/ __ \|   |  \  | (  <_> )\n'
        '/_______  /   __/|____(____  /___|  /__|  \____/\n'
        '        \/|__|             \/     \/            \n'
    )

def auth_manager():
    
    """
    gets an authentication token from Spotify with the following scopes:
    - read private playlists
    - modify private playlists
    
    API call(s):
    - POST
    """

    print('Authorizing...')
    
    scope = 'playlist-read-private playlist-modify-private'
    redirect_uri = 'http://localhost:8888'
    
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=redirect_uri))
    
    return sp


def get_playlist_id(sp, description) -> str:
    
    """
    gets playlist ID by name
    
    API call(s):
    - GET
    """
    
    # [BUG]
    # - description is case sensitive
    # - description string is too strict
    
    # [TODO]
    # - add option to search for playlist name
    
    print('Getting playlist ID...')

    try:
        playlists = sp.current_user_playlists()
    
        for playlist in playlists['items']:
            if playlist['description'] != None and playlist['description'] == description:
                return playlist['id']
        else:
            raise AttributeError

    except AttributeError:
        print(f'ERROR: "{description}" not found in playlists')
    except Exception:
        print('ERROR: Could not retrieve playlist ID')


def get_playlist_tracks(sp, playlist_id):
    
    """
    gets all tracks from specified playlist ID
    
    a track object consists of:
    - track_id
    - track_name
    - track_added_date
    - track_uri
    
    API call(s):
    - GET
    """

    playlist_items = sp.playlist_items(playlist_id=playlist_id)
    
    track_list = []
    
    for track_data in playlist_items['items']:

        track = {
            'track_id': track_data['track']['id'],
            'track_name': track_data['track']['name'],
            'track_added_date': track_data['added_at'],
            'track_uri': track_data['track']['uri']
        }
        
        track_list.append(track)
        
    return track_list


def filter_old_tracks(track_list):
    
    """
    filters old tracks from given list
    (filter criteria: older than 1 week)
    """

    week = datetime.timedelta(weeks=1) # defining one week
    week_ago = datetime.datetime.today() - week # subtract today with a week => last week
    
    old_counter, new_counter = 0,0
    old_track_list, new_track_list = [], []

    for track in track_list:
        
        track_date = track['track_added_date']
        track_date = track_date.split('T')
        
        # parse track_added_date string into datetime
        track_date = datetime.datetime.strptime(track_date[0], '%Y-%m-%d')
        
        if track_date < week_ago:
            # old tracks
            old_counter+=1
            old_track_list.append(track['track_uri'])
        else:
            # new tracks
            new_counter+=1
            new_track_list.append(track['track_name'])
    
    if old_counter == 1:
        print(f'\nFound {old_counter} song older than a week')
    else:
        print(f'\nFound {old_counter} songs older than a week')
        
    if new_counter == 1:
        print(f'{new_counter} song is still fresh')
    else:
        print(f'{new_counter} songs are still fresh')
        
    if new_counter >= 1:
        print(f'\n_____________________________________\n'
            'You got some songs left to listen to: \n')
        
        for fresh_track in new_track_list:
            print(f'- {fresh_track}')
        
        print('_____________________________________')
    
    return old_track_list


def delete_tracks(sp, playlist_id, tracks):
    
    """
    removes tracks from playlist with given ID
    
    API call(s):
    - DELETE
    """

    track_entries = []

    for track in tracks:
        track_entries.append(track)
        
    inp_validation = input('\n\nAre you sure you want to clear your playlist of old songs? (y/n): ').lower()
    
    if inp_validation == 'y':
        sp.playlist_remove_all_occurrences_of_items(playlist_id, items=track_entries)
        sp.playlist_remove_specific_occurrences_of_items(playlist_id, items=track_entries)
        print('Playlist has been cleared of old songs.')
    else:
        print('Aborted!')


if __name__ == '__main__':
    main()
