""" Generates some various randomised tests for speed checking """

from random import randint
import subprocess
from timeit import timeit
import datetime

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


if __name__ == '__main__':
    x = 0
    for i in range(100):
        print(i)
        x += timeit("print(subprocess.check_output(['python', 'reMatcher.py', 'c*ab{9}ac*', 'tests/cabac/cabac%d.txt']))" % i,
                     number=3, setup='import subprocess')

    avgTime = x / 100
    print("Average time: %f" % avgTime)

    fp = open("tests/testdata/cabacTests.txt", "a")

    def csvFormat(avgTime, testType):
        date = "{:%Y-%m-%d}".format(datetime.date.today())
        time = "{:%H:%M:%S}".format(datetime.datetime.now())
        return "%s,%s,%f,%s\n" % (date, time, avgTime, testType)


    fp.write(csvFormat(avgTime, "Python re Module"))
    fp.close()
