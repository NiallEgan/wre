import os
import sys
import re

def readFile(filename):
    fp = os.open(filename, os.O_RDONLY, 0777)
    f = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        f += read
    os.close(fp)
    return f

if __name__ == '__main__':
    try:
        regEx = sys.argv[1]
        s = readFile(sys.argv[2])
    except IndexError:
        print("No file name supplied")

    p = re.compile(regEx)
    p.match(s)

