import argparse
import pathlib


def get_core_parser():
    """
    Sub-parser containing core database module arguments.
    """
    core_parser = argparse.ArgumentParser(add_help=False)

    database_args = core_parser.add_argument_group(title="database arguments")
    database_args.add_argument(
        "-N", "--db-name", type=str, default="yam", metavar="<database_name>",
        help="Database name"
    )
    database_args.add_argument(
        "-C", "--dialect", type=str, default="postgresql", metavar="<dialect>",
        help="SQL dialect"
    )
    database_args.add_argument(
        "-R", "--driver", type=str, metavar="<driver>",
        help="SQL dialect driver"
    )
    database_args.add_argument(
        "-H", "--host", type=str, default="localhost", metavar="<host>",
        help="Database hostname"
    )
    database_args.add_argument(
        "-P", "--password", type=str, metavar="<password>",
        help="Database password"
    )
    database_args.add_argument(
        "-O", "--port", type=int, metavar="<port>", help="Database port number"
    )
    database_args.add_argument(
        "-U", "--user", type=str, metavar="<username>",
        help="Database user name"
    )
    return core_parser


def get_parser():
    core_parser = get_core_parser()
    parser = argparse.ArgumentParser(
        parents=[core_parser],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="",
    )

    action_group = parser.add_argument_group("actions")
    action_args = action_group.add_mutually_exclusive_group()
    action_args.add_argument(
        "-d", "--delete", action="store_true", help="Delete all rows"
    )
    action_args.add_argument(
        "-r", "--drop", action="store_true", help="Drop all tables"
    )
    action_args.add_argument(
        "-o", "--output", type=pathlib.Path, help="Path to JSON output file"
    )
    return parser
