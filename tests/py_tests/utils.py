import os

def getTestFilename(filename: str) -> str:
    testDir, _ = os.path.split(__file__)
    return os.path.join(testDir, "test_descr", filename)