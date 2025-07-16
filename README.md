Backup and Restore Jellyfin Playtimes via it's API

`jellyplaybackup.py` scrapes all playtime, watched and favorite data from every movie & show in the library, on a per-user basis, and stores it in a .json backup.

`jellyplayrestore.py` will write the .json backup data to the jellyfin server. It will ask which user's data you want to restore, and to which user you want to restore it to.

If you edit the configuration section of the scripts, you can specify your URL, API key and backup file location, so you don't get prompted for it each time.

DONT leave a trailing slash in the URL. It should be "http://localhost:8096" and NOT "http://localhost:8096/". It will give 404 errors if you leave the slash.

The scripts don't care what user or library your watch data is coming from or going to. You can decide.

`jellyplaytime.json` backup file will contain the IMDB, TMDB and TVDB IDs, in addition to the original internal ItemId. `jellyplayrestore.py` restores data based on the IMDB, TMDB and TVDB ID's and NOT ItemId. The internal Jellyfin ItemId's will be different in every installation of jellyfin. Restoring it based on IMDB means it doesn't matter what the internal ItemId is on the new server. These scripts don't care which users or installations your data is coming from or going to. You can choose.

It keeps verbose logs so you know what happened. Remember to backup your library.db. But this uses the API so it shouldn't screw anything up except maybe your watchtimes. Maybe delete the logs if you did a big job or many jobs.

Jellyfin's API doesnt appear to allow queries based on IMDB, so the `jellyplayrestore.py` script will retrieve a list of ALL media's ItemId's which returns their associated IMDB/TVDB/TMDB IDs. It can then cross-reference the new target ItemId based on the consistent IMDB ID. If you know of a way to improve the efficiency here, i'd be happy to hear.

You can also use this to move watch data from one user to another, by backing up the watch data and restoring whichever user's data, to whichever user you like.
