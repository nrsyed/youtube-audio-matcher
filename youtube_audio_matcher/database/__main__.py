import json

import youtube_audio_matcher.database
from ._argparsers import get_parser


def cli():
    parser = get_parser()
    args = parser.parse_args()

    db = youtube_audio_matcher.database.Database(
        user=args.user, password=args.password, db_name=args.db_name,
        host=args.host, port=args.port, dialect=args.dialect,
        driver=args.driver
    )

    if args.output:
        db_dict = db.as_dict()
        with open(args.output, "w") as f:
            json.dump(db_dict, f, indent=2)
    elif args.delete:
        db.delete_all()
    elif args.drop:
        db.drop_all_tables()
    elif args.songs:
        songs = db.query_songs()
        songs_str = json.dumps(songs, indent=2)
        print(songs_str)
