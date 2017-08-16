# Just a lightweight program to use reTests.py for now

from weightedRegex import *
from rigs import *
from parser import *
from reTests import *
import subprocess

class TestFailure(Exception):
    pass

if __name__ == '__main__':
    testsPassed = 0
    for (i, test) in enumerate(tests):
        print("TEST %d:" % i)
        print(test)
        print("\n")

        regex = test[0]
        string = test[1]
        result = subprocess.check_output(['./main-cNoJIT', regex, string])

        try:
            if int(result) !=  test[2]:
                print(test)
                print(result)
                print("Failed")
                raise TestFailure()
            else:
            #    print(test)
                print("Passed")

            testsPassed += 1
        except ValueError as e:
            if test[2] == SYNTAX_ERROR:
                testsPassed += 1
            else:
                #    print(test)
                print("Syntax Error : %s" % e.message)
                raise TestFailure()
    print("\nALL %d TESTS PASSED\n" % testsPassed)
