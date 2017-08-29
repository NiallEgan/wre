import os
import sys
from parser import compileRegex, ReSyntaxError, compilePartial
from weightFunctions import createSingleSymbolMatch, createStartPositionMatcher, createStartEndPositionMatcher
from rigs import BitRig, StartPositionRig, StartEndPositionRig
from rpython.rlib.jit import JitDriver

jitdriver = JitDriver(reds=["i", "string", "ans", "prevAns"], greens=["mode", "r", "rig"])
nModes = 5
PARTIAL_MATCH, COMPLETE_MATCH, FIND_LEFTMOST_START,\
    FIND_LEFTMOST_RANGE, FIND_ALL = range(0, nModes)

def readFile(filename):  # A simple RPython function to read a file using file pointers
    fp = os.open(filename, os.O_RDONLY, 0777)
    f = ""
    while True:
        read = os.read(fp, 4096)
        if len(read) == 0:
            break
        f += read
    os.close(fp)
    return f

def run(re, s, mode):

    string = [(i, ord(s[i])) for i in range(len(s))]

    if mode == PARTIAL_MATCH:
        ast = compilePartial(re, BitRig(), createSingleSymbolMatch)
        ans = mainloop(ast, string, BitRig(), mode)
        if ans == [(1, 0)]:
            print(True)
        else:
            print(False)

    elif mode == COMPLETE_MATCH:
        ast = compileRegex(re, BitRig(), createSingleSymbolMatch)
        ans = mainloop(ast, string, BitRig(), mode)
        if ans == [(1, 0)]:
            print(True)
        else:
            print(False)

    elif mode == FIND_LEFTMOST_START:
        ast = compilePartial(re, StartPositionRig(), createStartPositionMatcher)
        ans = mainloop(ast, string, StartPositionRig(), mode)
        if ans == []:
            print(-1)
        else:
            print(ans[0][1])

    elif mode == FIND_LEFTMOST_RANGE:
        ast = compilePartial(re, StartEndPositionRig(), createStartEndPositionMatcher)
        ans = mainloop(ast, string, StartEndPositionRig(), mode)
        if ans == []:
            print((-1, -1))
        else:
            print(ans[0])

    elif mode == FIND_ALL:
        ast = compilePartial(re, StartEndPositionRig(), createStartEndPositionMatcher)
        print(mainloop(ast, string, StartEndPositionRig(), mode))

    else:
        raise ReSyntaxError("Un recognised mode: %d" % mode)

def entry_point(argv):
    try:
        try:
            re = argv[1]
            s = argv[2]
            if len(argv) == 4:
                s = readFile(argv[2])
            mode = int(argv[3])

            run(re, s, mode)
        except IndexError:
            print("Not enough arguments: run in the form re file mode")
            return 1
    except ValueError:
        print("Invalid mode option")
        return 1
    except ReSyntaxError as e:
        print("Syntax error")
        return 0

    return 0

def target(*args):
    return entry_point, None

def jitpolicy(driver):
    from rpython.jit.codewriter.policy import JitPolicy
    return JitPolicy()

def mainloop(r, string, rig, mode):
    """ Returns if string matches the regex r """

    if string == []:
        return [r.empty()]

    r.shift(rig.one, string[0])  # Want to shift in an initial mark to start the
    # NFA

    i = 0
    ans = [] # TODO: Add variables to red and green list
    prevAns = rig.zero

    while i < len(string) - 1:  # Main program loop

        jitdriver.can_enter_jit(mode=mode, r=r, rig=rig, i=i, prevAns=prevAns, string=string,  ans=ans)
        jitdriver.jit_merge_point(mode=mode, r=r, rig=rig, i=i, prevAns=prevAns, string=string,  ans=ans)

        r.updateFinal()  # Explicitly call update here, cache the values
    #    print((i+1, "%s" % chr(string[i+1][1]), r.final()))

        if mode ==  FIND_ALL:
            r.updateFinal()
            # Maybe be faster to use all?
            if r.final() == prevAns and prevAns[0] >= 0: # I.e. prevAns != zero or one
                # The longest leftmost match has been found. Reset FSM and start
                # from the character at the end of the match
        #        print(i+1)
                ans.append(r.final())
                r.reset()
                r.shift(rig.one, string[i])
                prevAns = rig.zero
            else:
                prevAns = r.final()
                r.shift(rig.zero, string[i+1])
                i += 1

        else:
            r.updateFinal()
            r.shift(rig.zero, string[i+1])
            i += 1

    # TODO:  Find a way to use fewer conditions
    r.updateFinal()
    if r.final()[0] >= 0:
        ans.append(r.final())

    return ans

# TODO:
    # Clean up main loop -
    # Sort out {} bug -
    # Add anchor support -
    # Test
    # Benchmark - optimise?
    # Clean up, document

if __name__ == '__main__':
    entry_point(sys.argv)
