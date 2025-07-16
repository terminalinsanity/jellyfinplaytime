Backup and Restore Jellyfin Playtimes via it's API

`jellyplaybackup.py` scrapes all playtime, watched and favorite data from every movie & show in the library, on a per-user basis, and stores it in a .json backup.

`jellyplayrestore.py` will write the .json backup data to the jellyfin server. It will ask which user's data you want to restore, and to which user you want to restore it to.

If you edit the configuration section of the scripts, you can specify your URL, API key and backup file location, so you don't get prompted for it each time.

It keeps verbose logs so you know what happened. Remember to backup your library.db. But this uses the API so it shouldn't screw anything up except maybe your watchtimes.

You can also use this to move watch data from one user to another, by backing up the watch data, and restoring whichever user's data, to whichever user you like.
