

class CipherSuite:

    def __init__(self):
        return

    def getEncryptionAlgorithm(self):
        raise NotImplementedError()

    def getHashFunction(self):
        raise NotImplementedError()

    def getCurve(self):
        raise NotImplementedError()

