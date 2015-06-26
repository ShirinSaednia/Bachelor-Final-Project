__author__ = 'shirin'

import re


def make_packets_dict():
    res = {}
    for line in open("message_template.msg"):
        results = re.match("^\t([^\t{}]+.+)", line)
        if results:
            aline = results.group(1)
            aline = aline.split()
            if aline[1] == "Fixed":
                res[(aline[1], int(aline[2][8:], 16))] = (aline[0], aline[3], aline[4])
            else:
                res[(aline[1], int(aline[2]))] = (aline[0], aline[3], aline[4])
    return res


if __name__ == "__main__":
    print make_packets_dict()
