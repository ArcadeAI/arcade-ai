# Spotify Toolkit


|             |                |
|-------------|----------------|
| Name        | spotify |
| Package     | arcade_spotify |
| Repository  | None   |
| Version     | 0.1.2      |
| Description | Arcade tools for Spotify  |
| Author      | dev@arcade-ai.com      |


| Tool Name   | Description                                                             |
|-------------|-------------------------------------------------------------------------|
| GetTrackFromId | Get information about a track |
| GetRecommendations | Get track (song) recommendations based on seed artists, genres, and tracks |
| GetTracksAudioFeatures | Get audio features for a list of tracks (songs) |
| AdjustPlaybackPosition | Adjust the playback position within the currently playing track. |
| SkipToPreviousTrack | Skip to the previous track in the user's queue, if any |
| SkipToNextTrack | Skip to the next track in the user's queue, if any |
| PausePlayback | Pause the currently playing track, if any |
| ResumePlayback | Resume the currently playing track, if any |
| StartTracksPlaybackById | Start playback of a list of tracks (songs) |
| GetPlaybackState | Get information about the user's current playback state, including track or episode, and active device. |
| GetCurrentlyPlaying | Get information about the user's currently playing track |
| PlayArtistByName | Plays a song by an artist and queues four more songs by the same artist |
| PlayTrackByName | Plays a song by name |
| GetAvailableDevices | Get the available devices |
| Search | Search Spotify catalog information |


### GetTrackFromId
Get information about a track

#### Parameters
- `track_id`*(string, required)* The Spotify ID of the track

---

### GetRecommendations
Get track (song) recommendations based on seed artists, genres, and tracks
If a provided target value is outside of the expected range, it will clamp to the nearest valid value.

#### Parameters
- `seed_artists`*(array, required)* A list of Spotify artist IDs to seed the recommendations with
- `seed_genres`*(array, required)* A list of Spotify genre IDs to seed the recommendations with
- `seed_tracks`*(array, required)* A list of Spotify track IDs to seed the recommendations with
- `limit`*(integer, optional)* The maximum number of recommended tracks to return
- `target_acousticness`*(number, optional)* The target acousticness of the recommended tracks (between 0 and 1)
- `target_danceability`*(number, optional)* The target danceability of the recommended tracks (between 0 and 1)
- `target_duration_ms`*(integer, optional)* The target duration of the recommended tracks in milliseconds
- `target_energy`*(number, optional)* The target energy of the recommended tracks (between 0 and 1)
- `target_instrumentalness`*(number, optional)* The target instrumentalness of the recommended tracks (between 0 and 1)
- `target_key`*(integer, optional)* The target key of the recommended tracks (0-11)
- `target_liveness`*(number, optional)* The target liveness of the recommended tracks (between 0 and 1)
- `target_loudness`*(number, optional)* The target loudness of the recommended tracks (in decibels)
- `target_mode`*(integer, optional)* The target mode of the recommended tracks (0 or 1)
- `target_popularity`*(integer, optional)* The target popularity of the recommended tracks (0-100)
- `target_speechiness`*(number, optional)* The target speechiness of the recommended tracks (between 0 and 1)
- `target_tempo`*(number, optional)* The target tempo of the recommended tracks (in beats per minute)
- `target_time_signature`*(integer, optional)* The target time signature of the recommended tracks
- `target_valence`*(number, optional)* The target valence of the recommended tracks (between 0 and 1)

---

### GetTracksAudioFeatures
Get audio features for a list of tracks (songs)

#### Parameters
- `track_ids`*(array, required)* A list of Spotify track (song) IDs

---

### AdjustPlaybackPosition
Adjust the playback position within the currently playing track.

Knowledge of the current playback state is NOT needed to use this tool as it handles
clamping the position to valid start/end boundaries to prevent overshooting or negative values.

This tool allows you to seek to a specific position within the currently playing track.
You can either provide an absolute position in milliseconds or a relative position from
the current playback position in milliseconds.

Note:
    Either absolute_position_ms or relative_position_ms must be provided, but not both.

#### Parameters
- `absolute_position_ms`*(integer, optional)* The absolute position in milliseconds to seek to
- `relative_position_ms`*(integer, optional)* The relative position from the current playback position in milliseconds to seek to

---

### SkipToPreviousTrack
Skip to the previous track in the user's queue, if any


---

### SkipToNextTrack
Skip to the next track in the user's queue, if any


---

### PausePlayback
Pause the currently playing track, if any


---

### ResumePlayback
Resume the currently playing track, if any


---

### StartTracksPlaybackById
Start playback of a list of tracks (songs)

#### Parameters
- `track_ids`*(array, required)* A list of Spotify track (song) IDs to play. Order of execution is not guarenteed.
- `position_ms`*(integer, optional)* The position in milliseconds to start the first track from

---

### GetPlaybackState
Get information about the user's current playback state, including track or episode, and active device.
This tool does not perform any actions. Use other tools to control playback.


---

### GetCurrentlyPlaying
Get information about the user's currently playing track


---

### PlayArtistByName
Plays a song by an artist and queues four more songs by the same artist

#### Parameters
- `name`*(string, required)* The name of the artist to play

---

### PlayTrackByName
Plays a song by name

#### Parameters
- `track_name`*(string, required)* The name of the track to play
- `artist_name`*(string, optional)* The name of the artist of the track

---

### GetAvailableDevices
Get the available devices


---

### Search
Search Spotify catalog information

Explanation of the q parameter:
    You can narrow down your search using field filters. The available filters are album, artist, track, year, upc, tag:hipster, tag:new, isrc, and genre. Each field filter only applies to certain result types.

    The artist and year filters can be used while searching albums, artists and tracks. You can filter on a single year or a range (e.g. 1955-1960).
    The album filter can be used while searching albums and tracks.
    The genre filter can be used while searching artists and tracks.
    The isrc and track filters can be used while searching tracks.
    The upc, tag:new and tag:hipster filters can only be used while searching albums. The tag:new filter will return albums released in the past two weeks and tag:hipster can be used to return only albums with the lowest 10% popularity.

    Example: q="remaster track:Doxy artist:Miles Davis"

#### Parameters
- `q`*(string, required)* The search query
- `types`*(array, required)* The types of results to return, Valid values are 'album', 'artist', 'playlist', 'track', 'show', 'episode', 'audiobook'
- `limit`*(integer, optional)* The maximum number of results to return
