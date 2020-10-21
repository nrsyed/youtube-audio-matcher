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
        db_json = db.as_dict()
        with open(args.output, "w") as f:
            json.dump(db_json, f, indent=2)
