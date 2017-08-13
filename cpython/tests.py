# Just a lightweight program to use reTests.py for now

from weightedRegex import *
from rigs import *
from parser import *
from reTests import *

class TestFailure(Exception):
    pass

if __name__ == '__main__':
    matchFunction = lambda c : lambda x : c == x
    countFunction = lambda c : lambda x : 1 if c == x else 0

    intRig = IntRig()
    boolRig = BoolRig()
    testsPassed = 0

    for (i, test) in enumerate(tests):
        print("TEST %d:" % i)
        print(test)
        print("\n")
        try:
            r = compilePartial(test[0], boolRig, matchFunction)
            matches = match(r, test[1], boolRig)
            if test[2] == SUCCEED and not matches:
                #print(test)
                print("Failed")
                raise TestFailure()
            elif test[2] == FAIL and matches:
            #    print(test)
                print("Passed")
                raise TestFailure

            testsPassed += 1
        except SyntaxError as e:
            if test[2] == SYNTAX_ERROR:
                testsPassed += 1
            else:
            #    print(test)
                print("Syntax Error : %s" % e.message)
                raise TestFailure()
    print("\nALL TESTS PASSED\n")
