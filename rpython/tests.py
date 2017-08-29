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

        m = {"True\n": 1, "False\n": 0}  # Nasty...
        regex = test[0]
        string = test[1]

        try:
            result = m[subprocess.check_output(["python", "main.py", regex, string, "0", "stringMode"])]
            if result !=  test[2]:
                print(test)
                print(result)
                print("Failed")
                raise TestFailure()
            else:
                print("Passed")

            testsPassed += 1
        except KeyError as e:
            print("Error caught")
            if test[2] == SYNTAX_ERROR:
                testsPassed += 1
            else:
                #    print(test)
                print("Syntax Error : %s" % e.message)
                raise TestFailure()
    print("\nALL %d TESTS PASSED\n" % testsPassed)
