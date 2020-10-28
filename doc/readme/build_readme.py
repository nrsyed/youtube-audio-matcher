"""
This is a simple build script for combining multiple markdown (text) files
using paradox-style @@include directives. This can be used to split a single
markdown file into several source files.
"""
import os
import re
import sys


def build_file(fpath, src_dir):
    """
    Args:
        fpath (str): Path to source file.
        src_dir (str): Path to directory containing all source files.
    """
    expr = r"@@include\[(.*)\]"

    lines = []
    with open(fpath, "r") as f:
        for line in f:
            if line.startswith("@@include"):
                match = re.search(expr, line)
                inc_fname = match.groups()[0]
                inc_fpath = os.path.join(src_dir, inc_fname)

                inc_lines = build_file(inc_fpath, src_dir)
                lines.extend(inc_lines)
            else:
                lines.append(line)
    return lines


if __name__ == "__main__":
    src_fpath = sys.argv[1]
    out_path = sys.argv[2]

    src_dir = os.path.split(src_fpath)[0]
    out_lines = build_file(src_fpath, src_dir)

    with open(out_path, "w") as f:
        f.writelines(out_lines)
