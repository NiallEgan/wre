class Queue(object):
    """ A basic queue class (in built not supported in RPython)
        uses standard reversed front, back approach for good
        amortized time
    """
    def __init__(self):
        self.front = []
        self.back = []

    def put(self, x):
        self.back.append(x)

    def dequeue(self):
        x = self.front.pop()
        if self.front == []:
            self.front = self.back
            self.back = []
            self.front.reverse()
        return x

    def queue(self):
        reversedFront = list(self.front)
        reversedFront.reverse()
        return reversedFront + self.back
