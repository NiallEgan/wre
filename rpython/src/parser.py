from queue import Queue  # Inbuilt Queue is not RPython, so use custom class
import copy
from weightedRegex import *
from weightFunctions import *


CONCAT_MARKER = -1
EPS_MARKER = -2
CASE_INSENSITIVE = -3
ESCAPED_SQUARE = -4

class ReSyntaxError(Exception):
    """ Simple class for a syntax error """
    def __init__(self, msg):
        print(msg)
    #    Exception.__init__(self, msg)  # Doesn't work in RPython?

def post2WExprTree(expr, rig, symGeneratingFunction, partialCompilation):
    """ Creates the (weighted) syntax tree from a postfix
        expression
    """
    pieceStack = []
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

            elif sym == ord("|"):  # Alternate
                pieceStack.append(Alt(pieceStack.pop(), pieceStack.pop(), rig))

            elif sym == ord("*"):  # Zero or more
                prevPiece = pieceStack.pop()
                if isinstance(prevPiece, Rep):
                    raise ReSyntaxError("* Repetition")
                else:
                    pieceStack.append(Rep(prevPiece, rig))

            elif sym == ord("+"):  # One or more
                prevPiece = pieceStack.pop()
                if isinstance(prevPiece, Plus):
                    raise ReSyntaxError("+ Repetition")
                else:
                    pieceStack.append(Plus(prevPiece, rig))

            elif sym == ord("?"):  # Zero or one
                pieceStack.append(Question(pieceStack.pop(), rig))

            elif sym == ord("{"):  # Repetition count
                frontN = -expr.pop()

                if expr.pop() == ord("}"):
                    # repeat exactly frontN times
                    if frontN == 0:
                        pieceStack.pop()
                        pieceStack.append(Eps(rig))
                    elif frontN == 1:
                        pass  # Correct?
                    else:
                        repeatingExpr = pieceStack.pop()
                        chain = repeatingExpr
                        for _ in range(frontN - 1):
                            chain = Seq(repeatingExpr.copy(), chain, rig)
                        pieceStack.append(chain)

                else:  # expr.pop() == ","
                    endN = expr.pop()
                    if endN == ord("}"):
                        # repeat endN or more times
                        if frontN != 0:
                            repeatingExpr = pieceStack.pop()
                            chain = repeatingExpr
                            for _ in range(frontN - 1):
                                chain = Seq(repeatingExpr.copy(), chain, rig)
                            pieceStack.append(Seq(chain,  Rep(repeatingExpr.copy(), rig), rig))
                        else:
                            pieceStack.append(Rep(pieceStack.pop(), rig))
                    else:
                        # repeat between frontN and endN times
                        endN = -endN
                        repeatingExpr = pieceStack.pop()
                        chain = repeatingExpr if frontN > 0 else Eps(rig)

                        for _ in range(frontN - 1):
                            chain = Seq(repeatingExpr.copy(), chain, rig)

                        for _ in range(endN - frontN):
                            chain = Seq(chain, Question(repeatingExpr.copy(), rig), rig)

                        expr.pop()  # Discard the "{"
                        pieceStack.append(chain)

            elif sym == ord("["):  # Character class
                classExp = []

                while True:
                    token = expr.pop()
                    if token == ord("]"):
                        break
                    classExp.append(token)

                classWeightFunction = generateCharacterClass(classExp, rig, symGeneratingFunction, caseInsensitive)
                pieceStack.append(Sym(classWeightFunction, rig))

            elif sym == ord("\\"):  # Escapes - character classes built at post conversion phase
                sym = expr.pop()
                pieceStack.append(Sym(symGeneratingFunction(sym, rig), rig, chr(sym)))

            elif sym == ord("."):  # "." matches everything except \n
               pieceStack.append(Sym(AllButNewLineMatcher(rig), rig, "."))

            elif sym == EPS_MARKER:
                pieceStack.append(Eps(rig))

            elif sym == CASE_INSENSITIVE:
                caseInsensitive = True

            else:  # Literal symbols
                if caseInsensitive:
                    pieceStack.append(Sym(CaseInsensitiveWrapper(symGeneratingFunction(ord(chr(sym).lower()),
                                      rig), rig), rig, chr(sym) + "CASE_INSENSITIVE"))
                else:
                    pieceStack.append(Sym(symGeneratingFunction(sym, rig), rig, chr(sym)))

        if len(pieceStack) != 1:
            raise ReSyntaxError("Syntax Error: Incorrect number of operands")

        return pieceStack[0]

    except IndexError:
        # TODO: Break errors into more specific cases
        raise ReSyntaxError("Compilation error")


def generateCharacterClass(classExp, rig, symGeneratingFunction, caseInsensitive):
    """ Generates a list of chars based off of classExp. Note that there is
        a potential of duplication of characters. This can affect things when
        using a weighted automata, by e.g. giving two ways for "a" to match
        [aa-z]  with the standard int semiring """

    if classExp == []:
        raise ReSyntaxError("Invalid character class")
    characterClass = []
    classExp = classExp

    invert = False

    while classExp:
        token = classExp.pop()
        upperBound = -1

        if token == ord("-"):
            try:
                upperBound = classExp.pop()  # Guard against literal - followed by char
                lowerBound = classExp.pop()
                if lowerBound == ord("^"):  # Literal -, invert
                    invert = True
                    characterClass.append(ord("-"))
                    characterClass.append(upperBound)
                else:
                    if upperBound < lowerBound:
                        raise ReSyntaxError("Invalid Character class")
                    # TODO: This approach will probably only work for a limited
                    #       set of characters... i.e. ascii
                    for i in range(lowerBound, upperBound + 1):
                        characterClass.append(i)
            except IndexError:  # A literal "-"
                characterClass.append(token)
                if upperBound != -1 and upperBound != ord("^"):
                    characterClass.append(upperBound)
                elif upperBound == ord("^"):
                    invert = True

        elif token == ESCAPED_SQUARE:
            characterClass.append(ord("]"))
        elif token == ord("^"):
            invert = True
        else:
            characterClass.append(token)

    classFunctions = [symGeneratingFunction(c, rig) for c in characterClass]
    if caseInsensitive:
        classFunctions = [CaseInsensitiveWrapper(o, rig) for o in classFunctions]

    classWeightFunction = SymbolClassMatch(classFunctions, rig)
    if invert:
        classWeightFunction = InvertWrapper(classWeightFunction, rig)

    return classWeightFunction

def insertConcats(regExp):
    """ Inserts concats and tokenises everythig to ints """
    output = []
    insertMode = True
    literalMode = False
    ops = ["|", "?", "*", "+", ")", "{"]

    for (i, char) in enumerate(regExp):
        output.append(ord(char))

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


def regexToPost(regExpPreConverted):
    """ Converts an infix regular expression to postfix """

    regExp = insertConcats(regExpPreConverted)
    regExp.reverse()  # top of stack at end of list

    outputQueue = Queue()
    opStack = []
    ops = [CONCAT_MARKER, ord("|"), ord("?"), ord("*"), ord("+")]
    prec = {CONCAT_MARKER: 1, ord("|") : 0, ord("?") : 2, ord("*") : 2,
            ord("+") : 2, ord("(") : -1, ord("{") : 1.5}
    escapes = {97: 7, 34: 34, 102: 12, 39: 39, 98: 8, 110: 10, 114: 13,
               116: 9, 118: 11, 92: 92}


    while regExp:
        token = regExp.pop()

        if token == ord("\\"):
            nextToken = regExp.pop()

            # Check for character classes, otherwise escape the character
            if nextToken == ord("w"):
                regExp += [93, 95, 57, 45, 48, 122, 45, 97, 90, 45, 65, 91]

            elif nextToken == ord("s"):
                regExp += [93, 12, 10, 13, 9, 32, 91]

            elif nextToken == ord("d"):
                regExp += [93, 57, 45, 48, 91]

            elif nextToken == ord("W"):
                regExp += [93, 95, 57, 45, 48, 122, 45, 97, 90, 45, 65, 94, 91]

            elif nextToken == ord("S"):
                regExp += [93, 12, 10, 13, 9, 32, 94, 91]

            elif nextToken == ord("D"):
                regExp += [93, 57, 45, 48, 94, 91]

            else:
                # TODO: parsing of octal and hex characters
                outputQueue.put(ord("\\"))
                outputQueue.put(escapes.get(nextToken, nextToken))

        elif token in ops: #doesn't treat like a single unit
            while opStack and prec[opStack[-1]] >= prec[token]:
                outputQueue.put(opStack.pop())
            opStack.append(token)

        elif token == ord("("):
            try:
                if regExp[-1] == ord(")"):
                    regExp.pop()
                    outputQueue.put(EPS_MARKER)
                elif regExp[-1] == ord("?"):
                    try:
                        if (regExp[-2], regExp[-3], regExp[-4]) == (CONCAT_MARKER, ord("i"), ord(")")):
                            outputQueue.put(CASE_INSENSITIVE)
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
                raise ReSyntaxError("Mismatched left paren")

        elif token == ord(")"):
            try:
                while opStack[-1] != ord("("):
                    outputQueue.put(opStack.pop())
                opStack.pop()
            except IndexError:
                raise ReSyntaxError("Misatched right paren")

        elif token == ord("{"):
            while opStack and prec[opStack[-1]] >= prec[token]:
                outputQueue.put(opStack.pop())
            outputQueue.put(ord("{"))

            #  Collect the rest of the repetition count
            n = 0
            while True:

                nextToken = regExp.pop()
                if nextToken >= 48 and nextToken <= 57:
                    n = n * 10 + nextToken - 48
                elif nextToken == ord(","):
                    outputQueue.put(-n)  # A horrible hack...
                    n = 0
                    outputQueue.put(nextToken)
                elif nextToken == ord("}"):
                    if n != 0:
                        outputQueue.put(-n)
                    outputQueue.put(nextToken)
                    break

        elif token == ord("["):
            outputQueue.put(token)
            # Parse into rpn
            hyphenFound = False
            while True:
                try:
                    nextToken = regExp.pop()

                    # TODO: Should be able to parse literal "]"
                    if nextToken == ord("-"):
                        hyphenFound = True

                    elif nextToken == ord("]"):
                        if hyphenFound:
                            outputQueue.put(ord("-"))
                        outputQueue.put(nextToken)
                        break

                    elif nextToken == ord("\\"):
                        try:
                            #  TODO: Create negative character classes inside character classes
                            escapedCharacter = regExp.pop()
                            if escapedCharacter == ord("]"):
                                outputQueue.put(ESCAPED_SQUARE)  # Will be dealt with when building character classes
                            elif escapedCharacter == ord("w"):
                                regExp += [95, 57, 45, 48, 122, 45, 97, 90, 45, 65]
                            elif escapedCharacter == ord("s"):
                                regExp += [12, 10, 13, 9, 32]
                            elif escapedCharacter == ord("d"):
                                regExp += [57, 45, 48]
                            else:
                                outputQueue.put(escapes.get(escapedCharacter, escapedCharacter))

                        except IndexError:
                            raise ReSyntaxError("Inappropriate escaped bracket")

                    else:
                        outputQueue.put(nextToken)
                        if hyphenFound:
                            outputQueue.put(ord("-"))
                            hyphenFound = False
                except IndexError:
                    raise ReSyntaxError("Mismatched [")

        else:
            outputQueue.put(token)

    while opStack:
        outputQueue.put(opStack.pop())

    output = outputQueue.queue()
    output.reverse()
    return output  # Python views the top of the stack
    # as the end of the list, so must reverse


def compileRegex(exp, rig, matchFunction):
    """ Creates a compiled regex tree """
    return post2WExprTree(regexToPost(exp), rig, matchFunction, False)

def compilePartial(exp, rig, matchFunction):
    """ Creates a regex tree which will accept partial matches """

    ast = post2WExprTree(regexToPost(exp), rig, matchFunction, True)

    arbStart = Rep(Sym(OneProducer(rig), rig, "arb - start"), rig)
    ast = Seq(arbStart, ast, rig)
    arbEnd = Rep(Sym(OneProducer(rig), rig, "arb - end"), rig)
    ast = Seq(ast, arbEnd, rig)

    return ast
