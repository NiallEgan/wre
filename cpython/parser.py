from Queue import Queue
import copy
from weightedRegex import *

CONCAT_MARKER = 1
EPS_MARKER = 2
CASE_INSENSITIVE = 3

class SyntaxError(Exception):
    def __init__(self, msg):
        super(SyntaxError, self).__init__(msg)

def post2WExprTree(expr, rig, symGeneratingFunction):
    """ Creates the (weighted) syntax tree from a postfix expression """
    pieceStack = []
    print(expr)
    caseInsensitive = False
    if not expr:
        return Eps(rig)
    try:
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
                            for _ in range(frontN - 1):
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

                classWeightFunction = generateCharacterClass(classExp[:], rig, symGeneratingFunction, caseInsensitive)
                pieceStack.append(Sym(classWeightFunction, rig, classExp))

            elif sym == "\\":  # Escapes - character classes built at post conversion phase
                pieceStack.append(Sym(symGeneratingFunction(expr.pop()), rig))

            elif sym == ".":  # "." matches everything except \n
                pieceStack.append(Sym(lambda x: rig.one if x != '\n' else rig.zero, rig, "."))

            elif sym == EPS_MARKER:
                pieceStack.append(Eps(rig))

            elif sym == CASE_INSENSITIVE:
            #    print("case inse")
                caseInsensitive = True

            else:  # Literal symbols
                if caseInsensitive:
                    pieceStack.append(Sym(makeCaseInsensitive(symGeneratingFunction(sym.lower())), rig, sym + "CASE_INSENSITIVE"))
                else:
                    pieceStack.append(Sym(symGeneratingFunction(sym), rig, sym))

        if len(pieceStack) != 1:
            raise SyntaxError("Syntax Error: Incorrect number of operands")
        return pieceStack[0]

    except IndexError:
        # TODO: Break errors into more specific cases
        raise SyntaxError("Compilation error")

def makeCaseInsensitive(weightFunction):
    return lambda c : weightFunction(c.lower())

def generateCharacterClass(classExp, rig, symGeneratingFunction, caseInsensitive):
    """ Generates a list of chars based off of classExp. Note that there is
        a potential of duplication of characters. This can affect things when
        using a weighted automata, by e.g. giving two ways for "a" to match
        [aa-z]  with the standard int semiring """

    characterClass = []
    classExp = classExp

    invert = False

    while classExp:
        token = classExp.pop()
        upperBound = None

        if token == "-":
            try:
                upperBound = classExp.pop()  # Guard against literal - followed by char
                lowerBound = classExp.pop()
                if lowerBound == "^":  # Literal -, invert
                    invert = True
                    characterClass.append("-")
                    characterClass.append(upperBound)
                else:
                    # TODO: This approach will probably only work for a limited
                    #       set of characters
                    for i in range(ord(lowerBound), ord(upperBound) + 1):
                        characterClass.append(chr(i))
            except IndexError:  # A literal "-"
                characterClass.append(token)
                if upperBound != None and upperBound != "^":
                    characterClass.append(upperBound)
                elif upperBound == "^":
                    invert = True

        elif token == "\]":  # A bit hacky, but never mind...
            characterClass.append("]")
        elif token == "^":
            invert = True
        else:
            characterClass.append(token)


    def flip(f):
        return lambda c: rig.zero if f(c) == rig.one else rig.one
    #  WARNING: Inverting a characterClass will not always lead
    #  to the expected results for none boolean rigs
    # TODO: Should really implement proper checking for this..., test with int rig

    classFunctions = map(symGeneratingFunction, characterClass)
    if caseInsensitive:
        #print("Making case insensitive")
        classFunctions = map(makeCaseInsensitive, classFunctions)

    classWeightFunction = lambda c : reduce(rig.plus,
                                        map(lambda f : f(c), classFunctions),
                                        rig.zero)
    if invert:
        classWeightFunction = flip(classWeightFunction)
    return classWeightFunction

def insertConcats(regExp):
    output = []
    insertMode = True
    literalMode = False
    ops = {"|", "?", "*", "+", ")", "{"}

    for (i, char) in enumerate(regExp):
        output.append(char)

        if char == "{" or char == "[":
            insertMode = False

        elif literalMode or (char != "|" and char != "(" and char != "\\"):
            if char == "}" or char == "]":
                insertMode = True
            if i + 1 < len(regExp) and regExp[i+1] not in ops and insertMode:
                output.append(CONCAT_MARKER)

        if char == "\\":
            literalMode = True
        else:
            literalMode = False

    return output


def regexToPost(regExp):
    """ Converts an infix regular expression to postfix """

    # TODO: Not very efficent, needs optimising
    regExp = list(insertConcats(regExp))[::-1]  # top of stack at end of list
    print("Ref exp with concats:", regExp[::-1])
    outputQueue = Queue()
    opStack = []
    ops = {CONCAT_MARKER, "|", "?", "*", "+"}
    prec = {CONCAT_MARKER: 1, "|" : 0, "?" : 2, "*" : 2, "+" : 2, "(" : -1,
            "{" : 1.5}
    escapes = {"n" : "\n", "\\" : "\\", "'" : "\'",
                   "\"" : "\"", "a" : "\a", "b" : "\b",
                   "f" : "\f", "r" : "\r", "t" : "\t",
                   "v" : "\v"}

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
                regExp += [']', '9', '-', '0', '[']

            elif nextToken == "W":
                regExp += [']', '_', '9', '-', '0', 'z', '-', 'a', 'Z', '-', 'A', '^', '[']

            elif nextToken == "S":
                regExp += [']', '\f','\n', '\r', '\t', ' ', '^', '[']

            elif nextToken == "D":
                regExp += [']', '9', '-', '0', '^', '[']

            else:
                # TODO: Find a better way of doing this, parsing of octal and hex characters
                outputQueue.put("\\")
            #    print(nextToken)
                outputQueue.put(escapes.get(nextToken, nextToken))

        elif token in ops: #doesn't treat like a single unit
            while opStack and prec[opStack[-1]] >= prec[token]:
                outputQueue.put(opStack.pop())
            opStack.append(token)

        elif token == "(":
            try:
                if regExp[-1] == ")":
                #    print("Inserting eps mark")
                    regExp.pop()
                    outputQueue.put(EPS_MARKER)
                elif regExp[-1] == "?":
                #    print("searching for i")
                #    print(regExp[-2], regExp[-3], regExp[-4])
                    try:  # TODO: Make so that the concat markers never get put in to begin wtih
                        if (regExp[-2], regExp[-3], regExp[-4]) == (1, "i", ")"):
                            outputQueue.put(CASE_INSENSITIVE)
                    #        print("MARK MADE")
                            regExp.pop() # 1
                            regExp.pop() # ?
                            regExp.pop() # i
                            regExp.pop() # )
                            regExp.pop() # 1
                        else:
                            opStack.append(token)
                    except IndexError:
                        opStack.append(token)
                else:
                    opStack.append(token)
            except IndexError:
                raise SyntaxError("Mismatched left paren")

        elif token == ")":
            try:
                while opStack[-1] != "(":
                    outputQueue.put(opStack.pop())
                opStack.pop()
            except IndexError:
                raise SyntaxError("Misatched right paren")

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
                try:
                    nextToken = regExp.pop()

                    # TODO: Should be able to parse hyphens as literals if appropriate
                    if nextToken == "-":
                        hyphenFound = True

                    elif nextToken == "]":
                        if hyphenFound:
                            outputQueue.put("-")
                        outputQueue.put(nextToken)
                        break

                    elif nextToken == "\\":

                        try:
                            #  TODO: Create classes for negative
                            escapedCharacter = regExp.pop()
                            if escapedCharacter == "]":
                                outputQueue.put("\]")  # Will be dealt with when building character classes
                            elif escapedCharacter == "w":
                                regExp += list('_9-0z-aZ-A')
                            elif escapedCharacter == "s":
                                regExp += list('\x0c\n\r\t')
                            elif escapedCharacter == "d":
                                regExp += list('9-0')
                            else:
                                outputQueue.put(escapes.get(escapedCharacter, escapedCharacter))

                        except IndexError:
                            raise SyntaxError()  # TODO: Put in error messages

                    else:
                        outputQueue.put(nextToken)
                        if hyphenFound:
                            outputQueue.put("-")
                            hyphenFound = False
                except IndexError:
                    raise SyntaxError("Mismatched [")

        else:
            outputQueue.put(token)

    while opStack:
        outputQueue.put(opStack.pop())

    return list(outputQueue.queue)[::-1]  # Python views the top of the stack
    # as the end of the list, so must reverse


def compileRegex(exp, rig, matchFunction):
    """ Creates a compiled regex tree """
    return post2WExprTree(regexToPost(exp), rig, matchFunction)

def compilePartial(exp, rig, matchFunction):
    """ Creates a regex tree which will accept partial matches """
    return post2WExprTree(regexToPost(".*(" + exp + ").*"), rig, matchFunction)
