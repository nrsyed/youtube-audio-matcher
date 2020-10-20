import argparse


def get_core_parser():
    """
    Sub-parser containing core database module arguments.
    """
    core_parser = argparse.ArgumentParser(add_help=False)

    database_args = core_parser.add_argument_group(title="Database arguments")
    database_args.add_argument(
        "-C", "--dialect", type=str, default="postgresql", metavar="<dialect>",
        help="SQL dialect"
    )
    database_args.add_argument(
        "-H", "--host", type=str, default="localhost", metavar="<host>",
        help="Database hostname"
    )
    database_args.add_argument(
        "-N", "--db-name", type=str, default="yam", metavar="<database_name>",
        help="Database name"
    )
    database_args.add_argument(
        "-O", "--port", type=int, metavar="<port>", help="Database port number"
    )
    database_args.add_argument(
        "-P", "--password", type=str, metavar="<password>",
        help="Database password"
    )
    database_args.add_argument(
        "-R", "--driver", type=str, metavar="<driver>",
        help="SQL dialect driver"
    )
    database_args.add_argument(
        "-U", "--user", type=str, metavar="<username>",
        help="Database user name"
    )
    return core_parser
