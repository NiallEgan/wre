""" Generates some various randomised tests for speed checking """

from random import randint
import subprocess
from timeit import timeit
import datetime

RE, JIT, RE2 = range(3)

def genCabacTests():
    def cabac(x):
        """ Returns a string of the form c{0, 100000}ab{x}ac{0, 100000} """

        start = randint(0, 100000)
        end = randint(0, 100000)

        return "c" * start + "a" + "b" * x + "a" + "c" * end

    for i in range(100):
        f = open("tests/cabac/cabac%d.txt" % i, 'w')
        f.write(cabac(9))
        f.close()


def testCabac():
    x = 0
    mode = 1
    for i in range(100):
        print(i)
        if mode == 0:
            x += timeit(
                "print(subprocess.check_output(['python', 'tests/src/reMatcher.py', 'ab{9}a', 'tests/tests/cabac/cabac%d.txt']))" % i,
                number=3, setup='import subprocess')
        else:
            x += timeit("print(subprocess.check_output(['./jit', 'ab{9}a', 'tests/tests/cabac/cabac%d.txt', '4']))" % i,
                        number=3, setup='import subprocess')

    avgTime = x / 100
    print("Average time: %f" % avgTime)

    fp = open("tests/testdata/cabacPositionTests.txt", "a")

    def csvFormat(avgTime, testType):
        date = "{:%Y-%m-%d}".format(datetime.date.today())
        time = "{:%H:%M:%S}".format(datetime.datetime.now())
        return "%s,%s,%f,%s\n" % (date, time, avgTime, testType)

    fp.write(csvFormat(avgTime, "jit - ab{9}a"))
    fp.close()

def genATests(n):
    for i in range(1, n+1):
        f = open("tests/tests/a/a%d.txt" % i, 'w')
        f.write("a" * i)
        f.close()




def testA(n, mode):
    results = []

    for i in range(1, n+1):
        print(i)
        if mode == RE:
            results.append(timeit("print(subprocess.check_output(['python', 'tests/src/reMatcher.py', '(a?){%d}a{%d}', 'tests/tests/a/a%d.txt']))" % (i, i, i),
                        number=10, setup='import subprocess') / 10)
        elif mode == JIT:
            results.append(timeit(r"print(subprocess.check_output(['./jit', r'(a?){%d}a{%d}', 'tests/tests/a/a%d.txt', '4']))" % (i, i, i),
                        number=1000, setup='import subprocess') / 1000)

        elif mode == RE2:
            results.append(timeit(
                "print(subprocess.check_output(['python', 'tests/src/re2Tests.py', '(a?){%d}a{%d}', 'tests/tests/a/a%d.txt']))" % (i, i, i),
                number=1000, setup='import subprocess') / 1000)

    def csvFormat(n, time):
        return "%d, %f\n" % (n, time)

    if mode == RE:
        csvFile = open("tests/testdata/anTestsRe.csv", "a")
    elif mode == JIT:
        csvFile = open("tests/testdata/anTestsJit.csv", "a")
    elif mode == RE2:
        csvFile = open("tests/testdata/anTestsRe2.csv", "a")

    for i in range(n):
        csvFile.write(csvFormat(i+1, results[i]))

    csvFile.close()

def testWikiXML(mode):
    print(mode)
    nReps = 10

    if mode == RE:
        result = timeit(
            "print(subprocess.check_output(['python', 'tests/src/reMatcher.py', '([a-zA-Z][a-zA-Z0-9]*)://([^ /]+)(/[^ ]*)?|([^ @]+)@([^ @]+)', 'tests/tests/wikipages.xml']))",
             number=nReps, setup='import subprocess') / nReps
    elif mode == JIT:
        result = timeit("print(subprocess.check_output(['./jit', '([a-zA-Z][a-zA-Z0-9]*)://([^ /]+)(/[^ ]*)?|([^ @]+)@([^ @]+)', 'tests/tests/wikipages.xml', '4']))",
                        number=nReps, setup='import subprocess') / nReps
    elif mode == RE2:
        result = timeit(
            "print(subprocess.check_output(['python', 'tests/src/re2Tests.py', '([a-zA-Z][a-zA-Z0-9]*)://([^ /]+)(/[^ ]*)?|([^ @]+)@([^ @]+)', 'tests/tests/wikipages.xml']))",
            number=nReps, setup='import subprocess') / nReps

    csvFile = open("tests/testdata/wikiTest.csv", "a")

    name = ["re", "jit", "re2"]

    print(result)
    csvFile.write("%f,%s\n" % (result, name[mode]))

if __name__ == '__main__':
    print("foo")
    for i in range(3):
        testWikiXML(i)
