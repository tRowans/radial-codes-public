import numpy as np

class Code:
    def condense_rows(self,matrix):
        condensed_matrix = [list(np.nonzero(row)[0]) for row in matrix]
        return condensed_matrix

    def condense_columns(self,matrix):
        condensed_matrix = [list(np.nonzero(row)[0]) for row in matrix.T]
        return condensed_matrix

    def __init__(self, r, s, HX, HZ, LX, LZ):
        self.r = r
        self.s = s
        self.checkToBitsX = self.condense_rows(HX)
        self.checkToBitsZ = self.condense_rows(HZ)
        self.bitToChecksX = self.condense_columns(HX)
        self.bitToChecksZ = self.condense_columns(HZ)
        self.logicalsX = self.condense_rows(LX)
        self.logicalsZ = self.condense_rows(LZ)

        self.N = len(HX[0])
        self.nX = HX.shape[0]
        self.nZ = HZ.shape[0]
