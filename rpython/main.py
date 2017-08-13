import os
import sys
from parser import compileRegex
from weightFunctions import createSingleSymbolMatch
from rigs import BoolRig

def run(fp):
    f = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        f += read
        os.close(fp)
    # TODO: Create a rig syntax in the file...
    string = []
    regExp = ""
    addToString = True
    for char in f:
        if char == "\n":
            addToString = False
        elif addToString:
            string.append(ord(char))
        else:
            regExp += char
    ast = compileRegex(regExp, BoolRig(), createSingleSymbolMatch)

    mainloop(ast, string, BoolRig())


def entry_point(argv):
    try:
        filename = argv[1]
    except IndexError:
        print("No file name supplied")
        return 1

    run(os.open(filename, os.O_RDONLY, 0777))
    return 0

def target(*args):
    return entry_point, None

def mainloop(r, string, rig):
    """ Returns if string matches the regex r """

    if string == []:
        return r.empty()

    r.shift(rig.one, string[0])  # Want to shift in an initial mark to start the
    # NFA

    i = 0
    while i < len(string) - 1:  # Main program loop
        c = string[i + 1]
        r.updateFinal()  # Explicitly call update here, cache the values
        r.shift(rig.zero, c)
        i += 1

    r.updateFinal()
    return r.final()

if __name__ == '__main__':
    entry_point(sys.argv)
