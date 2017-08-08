from weightedRegex import *
from rigs import *
from parser import *

if __name__ == '__main__':
    matchFunction = lambda c : lambda x : c == x
    countFunction = lambda c : lambda x : 1 if c == x else 0

    intRig = IntRig()
    boolRig = BoolRig()
    exp = "\d*abc+|alphabet"
    print(insertConcats(exp))
    r = post2WExprTree(regexToPost(exp), boolRig, matchFunction)
    print(match(r, "alphabet", boolRig))
