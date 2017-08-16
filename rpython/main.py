import os
import sys
from parser import compileRegex, ReSyntaxError, compilePartial
from weightFunctions import createSingleSymbolMatch
from rigs import BoolRig, BitRig
from rpython.rlib.jit import JitDriver

jitdriver = JitDriver(reds=["i", "string", "rig"], greens=["r"])

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

def run(re, s):

    # TODO: Create a rig syntax in the file...
    string = [ord(c) for c in s]
    try:
        ast = compilePartial(re, BitRig(), createSingleSymbolMatch)
        return mainloop(ast, string, BitRig())
    except ReSyntaxError:
        print("Syntax Error caught")
        return 0


def entry_point(argv):
    try:
        re = argv[1]
        s = readFile(argv[2])
    except IndexError:
        print("No file name supplied")
        return 1

    print(run(re, s))

    return 0

def target(*args):
    return entry_point, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()



def mainloop(r, string, rig):
    """ Returns if string matches the regex r """

    if string == []:
        return r.empty()

    r.shift(rig.one, string[0])  # Want to shift in an initial mark to start the
    # NFA

    i = 0
    while i < len(string) - 1:  # Main program loop
        jitdriver.can_enter_jit(r=r, i=i, string=string, rig=rig)
        jitdriver.jit_merge_point(r=r, i=i, string=string, rig=rig)

        r.updateFinal()  # Explicitly call update here, cache the values
        r.shift(rig.zero, string[i+1])
        i += 1

    r.updateFinal()
    return r.final()

if __name__ == '__main__':
    entry_point(sys.argv)
