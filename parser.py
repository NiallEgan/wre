from Queue import Queue
import copy
from weightedRegex import *

CONCAT_MARKER = 1

def post2WExprTree(expr, rig, symGeneratingFunction):
    """ Creates the (weighted) syntax tree from a postfix expression """
    pieceStack = []
    print(expr)

    while expr:
        sym = expr.pop()

        if sym == CONCAT_MARKER:  # Concat
            expr2 = pieceStack.pop()
            expr1 = pieceStack.pop()
            pieceStack.append(Seq(expr1, expr2, rig))

        elif sym == "|":  # Alternate
            pieceStack.append(Alt(pieceStack.pop(), pieceStack.pop(), rig))

        elif sym == "*":  # Zero or more
            pieceStack.append(Rep(pieceStack.pop(), rig))

        elif sym == "+":  # One or more
            pieceStack.append(Plus(pieceStack.pop(), rig))

        elif sym == "?":  # Zero or one
            pieceStack.append(Question(pieceStack.pop(), rig))

        elif sym == "{":  # Repetition count
            # TODO: This part could do with some serious optimisation
            frontN = int(expr.pop())

            if expr.pop() == "}":
                # repeat exactly endN times
                if frontN == 0:
                    pieceStack.pop()
                    pieceStack.append(Eps(rig))
                elif frontN == 1:
                    pass
                else:
                    repeatingExpr = pieceStack.pop()
                    chain = repeatingExpr
                    for _ in range(endN - 1):
                        chain = Seq(copy.deepcopy(repeatingExpr), chain, rig)
                    pieceStack.append(chain)

            else:  # expr.pop() == ","
                endN = expr.pop()
                if endN == "}":
                    # repeat endN or more times
                    if frontN != 0:
                        repeatingExpr = pieceStack.pop()
                        chain = repeatingExpr
                        for _ in range(endN - 1):
                            chain = Seq(copy.deepcopy(repeatingExpr), chain, rig)
                        pieceStack.append(Seq(chain,  Rep(copy.deepcopy(repeatingExpr), rig), rig))
                    else:
                        pieceStack.append(Rep(pieceStack.pop(), rig))
                else:
                    # repeat between frontN and endN times
                    endN = int(endN)
                    repeatingExpr = pieceStack.pop()
                    chain = repeatingExpr if frontN > 0 else Eps(rig)

                    for _ in range(frontN - 1):
                        chain = Seq(copy.deepcopy(repeatingExpr), chain, rig)

                    for _ in range(endN - frontN):
                        chain = Seq(chain, Question(copy.deepcopy(repeatingExpr), rig), rig)

                    expr.pop()  # Discard the "{"
                    pieceStack.append(chain)

        elif sym == "[":  # Character class
            classExp = []

            while True:
                token = expr.pop()
                if token == "]":
                    break
                classExp.append(token)

            characterClass = generateCharacterClass(classExp)
            classFunctions = map(symGeneratingFunction, characterClass)
            classWeightFunction = lambda c : reduce(rig.plus,
                                                    map(lambda f: f(c), classFunctions),
                                                    rig.zero)
            pieceStack.append(Sym(classWeightFunction, rig))

        elif sym == "\\":  # Escapes - character classes built at post conversion phase
            pieceStack.append(Sym(symGeneratingFunction(expr.pop()), rig))

        else:  # Literal symbols
            pieceStack.append(Sym(symGeneratingFunction(sym), rig))

    assert len(pieceStack) == 1
    return pieceStack[0]

def generateCharacterClass(classExp):
    """ Generates a list of chars based off of classExp. Note that there is
        a potential of duplication of characters. This can affect things when
        using a weighted automata, by e.g. giving two ways for "a" to match
        [aa-z]  with the standard int semiring """

    characterClass = []
    classExp = classExp

    while classExp:
        token = classExp.pop()
        if token == "-":
            upperBound = classExp.pop()
            lowerBound = classExp.pop()

            # TODO: This approach will probably only work for a limited
            #       set of characters
            for i in range(ord(lowerBound), ord(upperBound) + 1):
                characterClass.append(chr(i))
        else:
            # TODO: Think about escaped characters here
            characterClass.append(token)
    return characterClass

def insertConcats(regExp):
    output = []
    insertMode = True
    ops = {".", "|", "?", "*", "+", ")"}

    for (i, char) in enumerate(regExp):
        output.append(char)

        if char == "{" or char == "[":
            insertMode = False

        elif char != "|" and char != "(" and char != "\\":
            if char == "}" or char == "]":
                insertMode = True
            if i + 1 < len(regExp) and regExp[i+1] not in ops and insertMode:
                output.append(CONCAT_MARKER)

    return output


def regexToPost(regExp):
    """ Converts an infix regular expression to postfix """

    # TODO: Not very efficent, needs optimising
    regExp = list(insertConcats(regExp))[::-1]  # top of stack at end of list
    outputQueue = Queue()
    opStack = []
    ops = {CONCAT_MARKER, "|", "?", "*", "+"}
    prec = {CONCAT_MARKER: 1, "|" : 0, "?" : 2, "*" : 2, "+" : 2, "(" : -1,
            "{" : 1.5}

    while regExp:
        token = regExp.pop()

        if token == "\\":
            nextToken = regExp.pop()

            # Check for character classes, otherwise escape the character
            if nextToken == "w":
                regExp += [']', '_', '9', '-', '0', 'z', '-', 'a', 'Z', '-', 'A', '[']

            elif nextToken == "s":
                regExp += [']', '\f', '\n', '\r', '\t', ' ', '[']

            elif nextToken == "d":
                print("building digit class")
                regExp += [']', '9', '-', '0', '[']
            else:
                outputQueue.put(token)
                outputQueue.put(nextToken)
        elif token in ops:

            while opStack and prec[opStack[-1]] >= prec[token]:
                outputQueue.put(opStack.pop())
            opStack.append(token)

        elif token == "(":
            opStack.append(token)

        elif token == ")":
            while opStack[-1] != "(":
                outputQueue.put(opStack.pop())
            opStack.pop()

        elif token == "{":
            while opStack and prec[opStack[-1]] >= prec[token]:
                outputQueue.put(opStack.pop())
            outputQueue.put("{")

            #  Collect the rest of the repetition count
            while True:
                nextToken = regExp.pop()
                outputQueue.put(nextToken)
                if nextToken == "}":
                    break

        elif token == "[":
            outputQueue.put(token)
            # Parse into rpn
            hyphenFound = False
            while True:
                nextToken = regExp.pop()
                # TODO: Should be able to parse hyphens as literals if appropriate
                if nextToken == "-":
                    hyphenFound = True

                elif nextToken == "]":
                    if hyphenFound:
                        outputQueue.put("-")
                    outputQueue.put(nextToken)
                    break

                else:
                    outputQueue.put(nextToken)
                    if hyphenFound:
                        outputQueue.put("-")
                        hyphenFound = False

        else:
            outputQueue.put(token)

    while opStack:
        outputQueue.put(opStack.pop())

    return list(outputQueue.queue)[::-1]  # Python views the top of the stack
    # as the end of the list, so must reverse


def compileRegex(exp, rig, matchFunction):
    return post2WExprTree(regexToPost(exp), rig, matchFunction)
