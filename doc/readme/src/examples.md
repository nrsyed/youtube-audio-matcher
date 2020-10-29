### Add songs/fingerprints to the database

This command (which makes use of the package's `yam` command-line tool)
adds to the database (`-A`) a local file (`file1.mp3`), all files from a local
directory (`sample_directory`), and the first 60 seconds (`--duration 60`) of
audio from all videos on a YouTube channel (`www.youtube.com/c/sample_channel`),
excluding any videos shorter than 5 seconds (`-S 5`) or longer than 300 seconds
(`-L 300`), using the (PostgreSQL) database credentials `-U yam` (user `yam`),
`-N yam` (database name `yam`), and database password `yam` (`-P yam`).

**Command**:
```
yam -A www.youtube.com/c/sample_channel file1.mp3 sample_directory \
  -S 5 -L 300 --duration 60 -U yam -N yam -P yam
```

**Output**:
```
[INFO] Fingerprinted /home/sample_directory/file3.mp3 (44570 hashes)
[INFO] Fingerprinted /home/sample_directory/file2.mp3 (89020 hashes)
[INFO] Fingerprinted /home/file1.mp3 (216960 hashes)
[INFO] Successfully downloaded /home/Z6_7orLq0D.mp3
[INFO] Added /home/sample_directory/file3.mp3 to database (4.56 s)
[INFO] Fingerprinted /home/Z6_7orLq0D.mp3 (75470 hashes)
[INFO] Successfully downloaded /home/s71A5oUut3.mp3
[INFO] Successfully downloaded /home/wFoxOcQU60.mp3
[INFO] Added /home/sample_directory/file2.mp3 to database (9.04 s)
[INFO] Fingerprinted /home/wFoxOcQU60.mp3 (89020 hashes)
[INFO] Fingerprinted /home/s71A5oUut3.mp3 (216960 hashes)
[INFO] Added /home/Z6_7orLq0D.mp3 to database (8.06 s)
[INFO] Added /home/wFoxOcQU60.mp3 to database (8.89 s)
[INFO] Added /home/file1.mp3 to database (21.22 s)
[INFO] Added /home/s71A5oUut3.mp3 to database (19.88 s)
[INFO] All songs added to database (25.13 s)
```

### Match songs against the database

This command (which makes use of the package's `yam` command-line tool)
fingerprints a local file (`file4.mp3`) as well as downloads/fingerprints
audio from all videos on two YouTube users/channels
(`youtube.com/c/some_channel youtube.com/u/some_user`), excluding videos longer
than 600 seconds (`-L 300`), deletes any downloaded files after fingerprinting
(`-D`), and matches all fingerprints against those in the (PostgreSQL) database
with the database credentials `-U yam` (user `yam`), `-N yam`
(database name `yam`), and database password `yam` (`-P yam`).

**Command**:
```
yam youtube.com/c/some_channel youtube.com/u/some_user file4.mp3 \
  -L 600 -D -U yam -N yam -P yam
```

The output contains matches (if any) as well as information on each match,
including the `confidence` (number of matching fingerprints divided by total
number of input song fingerprints) and `relative_offset` (which part of the
matched song the input song corresponds to, in seconds); in other words, a
`relative_offset` of 300 means that the beginning of the input song corresponds
to the 300-second mark in the matched song from the database.

**Output**:
```
[INFO] Fingerprinted /home/file4.mp3 (11520 hashes)
[INFO] Matching fingerprints for /home/file4.mp3
[INFO] Successfully downloaded /home/pzvDf_H7db.mp3
[INFO] Successfully downloaded /home/Rv4nWAZw8V.mp3
[INFO] Successfully downloaded /home/iPTmeNCao7.mp3
[INFO] Fingerprinted /home/pzvDf_H7db.mp3 (32650 hashes)
[INFO] Matching fingerprints for /home/pzvDf_H7db.mp3
[INFO] Fingerprinted /home/Rv4nWAZw8V.mp3 (22520 hashes)
[INFO] Matching fingerprints for /home/Rv4nWAZw8V.mp3
[INFO] Fingerprinted /home/iPTmeNCao7.mp3 (73860 hashes)
[INFO] Matching fingerprints for /home/iPTmeNCao7.mp3
[INFO] Finished matching fingerprints for /home/file4.mp3 in 10.28 s
[INFO] Finished matching fingerprints for /home/Rv4nWAZw8V.mp3 in 2.68 s
[INFO] Finished matching fingerprints for /home/iPTmeNCao7.mp3 in 7.21 s
[INFO] Finished matching fingerprints for /home/pzvDf_H7db.mp3 in 10.14 s
[INFO] Match 1:
{
    "youtube_id": null,
    "title": null,
    "duration": null,
    "channel_url": null,
    "path": "/home/file4.mp3",
    "filehash": "e0bf9d28e9b2409b7ad181b97f532569d27c9633",
    "num_fingerprints": 11520,
    "matching_song": {
        "id": 8,
        "duration": 436.0,
        "filehash": "c12b119ab98caee4a24eef5e7b3f4d7bf2b38f99",
        "filepath": "/home/song2.mp3",
        "title": null,
        "youtube_id": null,
        "num_fingerprints": 812890
    },
    "match_stats": {
        "num_matching_fingerprints": 3352,
        "confidence": 0.29097222222222224,
        "iou": 0.004082537409050274,
        "relative_offset": 300.0
    }
}

[INFO] Match 2:
{
    "youtube_id": "iPTmeNCao7",
    "title": "Sample YT video title",
    "duration": 177,
    "channel_url": "https://www.youtube.com/c/some_channel/videos",
    "path": "/home/iPTmeNCao7.mp3",
    "filehash": "6b59b4c301de5ad3f7dddcdb78fbf62bd1618cab",
    "num_fingerprints": 73860,
    "matching_song": {
        "id": 3,
        "duration": 155.0,
        "filehash": "6ba1139a7fc8cde33ff30065b45ed3c9f457f5a6",
        "filepath": "/home/a92_Uxy5mq.mp3",
        "title": "Some other video on youtube",
        "youtube_id": "a92_Uxy5mq",
        "num_fingerprints": 216960
    },
    "match_stats": {
        "num_matching_fingerprints": 73821,
        "confidence": 0.9994719740048741,
        "iou": 0.3401905077903585,
        "relative_offset": 0.0
    }
}
```

### Print all songs in the database

**Command**:
```
yamdb -s -U yam -N yam -P yam
```

**Output**:
```
[
  {
    "id": 3,
    "duration": 155.0,
    "filehash": "6ba1139a7fc8cde33ff30065b45ed3c9f457f5a6",
    "filepath": "/home/a92_Uxy5mq.mp3",
    "title": "Some other video on youtube",
    "youtube_id": "a92_Uxy5mq",
  },
  {
    "id": 8,
    "duration": 436.0,
    "filehash": "c12b119ab98caee4a24eef5e7b3f4d7bf2b38f99",
    "filepath": "/home/song2.mp3",
    "title": null,
    "youtube_id": null,
  }
]
```

### Drop all tables in the database
```
yamdb -r -U yam -N yam -P yam
```

### Plot a song's audio fingerprint/spectrogram

The `yamfp` tool was used to create the spectrogram/fingerprint figures in the
background section above.

```
yamfp /path/to/file.mp3
```

### Download audio from all videos on multiple YouTube channels

The YouTube audio download functionality from the `yam` command also exists
as a standalone command-line tool: `yamdl` (this simply downloads videos as MP3
files without fingerprinting them or interacting with the database in any way).

The following command downloads the first 30 seconds of audio (`--end 30`) from
all videos on two channels
(`youtube.com/user/ytuser youtube.com/c/somechannel/videos`), excluding
videos shorter than 7 seconds (`-S 7`) or longer than 20 minutes (`-L 1200`),
saves them to a specified directory (`-d /path/to/dest_dir`), skips any files
that already exist in the destination directory (`-i`), waits 4 seconds for
YouTube pages to load in the browser after each page scroll (`-p 4`) to ensure
the page has time to load and the entire page source is obtained/scraped
(increasing this wait time can help on slower internet connections), and
retries failed downloads up to 10 times (`-r 10`) in case youtube-dl fails
to download videos, which occasionally happens.

```
yamdl youtube.com/user/ytuser youtube.com/c/somechannel/videos \
  --end 30 -S 7 -L 1200 -d /path/to/dest_dir -i -p 4 -r 10
```

All `yamdl` options can also be used with `yam`.
