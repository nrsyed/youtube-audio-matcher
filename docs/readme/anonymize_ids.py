import os
import random
import re
import string
import sys


def random_str(inp):
    """
    Return a string of ``inp`` random characters (if ``inp`` is an int) or
    ``len(inp)`` random characters (if ``inp`` is a string).
    """
    if isinstance(inp, int):
        n = inp
    elif isinstance(inp, str):
        n = len(inp)
    else:
        raise ValueError("Invalid input (must be str or int)")
    chars = string.ascii_letters + string.digits + "_-"
    return "".join(random.sample(chars, n))


def replace_ids(fpath):
    """
    TODO
    """
    youtube_id_expr = r"([a-zA-Z0-9_-]{11})\.mp3"
    ytid_map = dict()

    lines = []
    with open(fpath, "r") as f:
        for line in f:
            match = re.search(youtube_id_expr, line)
            if match:
                youtube_id = os.path.splitext(match.groups()[0])[0]
                if youtube_id not in ytid_map:
                    ytid_map[youtube_id] = random_str(youtube_id[:-1])
                line = line.replace(youtube_id, ytid_map[youtube_id])
            lines.append(line)
    return lines


if __name__ == "__main__":
    fpath = sys.argv[1]
    lines = replace_ids(fpath)
    print("".join(lines))
