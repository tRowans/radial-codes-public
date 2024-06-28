import numpy as np
import csv
import sys
from matgen import matgen

class Circulant:
    def __init__(self, s, x):
        self.L = s
        self.shift = x

    def __mul__(self,other):
        if type(other) != Circulant and other != 0:
            raise Exception("Error: multiplication is only defined with other circulants or with zero")
        if type(other) == Circulant and other.L != self.L:
            raise Exception("Error: multiplication is not defined between circulants with different cycle lengths")
        if other != 0:
            return Circulant(self.L, (self.shift + other.shift) % self.L)
        else:
            return 0
    def __rmul__(self,other):
        if type(other) != Circulant and other != 0:
            raise Exception("Error: multiplication is only defined with other circulants or with zero")
        if type(other) == Circulant and other.L != self.L:
            raise Exception("Error: multiplication is not defined between circulants with different cycle lengths")
        if other != 0:
            return Circulant(self.L, (self.shift + other.shift) % self.L)
        else:
            return 0

    def inverse(self):
        return Circulant(self.L,(self.L - self.shift) % self.L)

    def to_binary(self):
        B = []
        for i in range(self.L):
            B.append([int((i + self.shift) % self.L == j) for j in range(self.L)])
        return B

def protograph_I(r,s):
    I = []
    for i in range(r):
        I_row = []
        for j in range(r):
            if i == j:
                I_row.append(Circulant(s,0))
            else:
                I_row.append(0)
        I.append(I_row)
    return I

def lifted_product(A,B,s):
    I = protograph_I(len(A),s)
    HX_left = np.kron(A,I)
    HX_right = np.kron(I,B)
    HX = np.hstack((HX_left,HX_right))

    A_star = np.array([[el.inverse() for el in row] for row in A.transpose()])
    B_star = np.array([[el.inverse() for el in row] for row in B.transpose()])
    HZ_left = np.kron(I,B_star)
    HZ_right = np.kron(A_star,I)
    HZ = np.hstack((HZ_left,HZ_right))

    return HX, HZ

def protograph_to_binary_matrix(protograph,s):
    binary_matrix = []
    for row in protograph:
        binary_row = []
        for i in row:
            if i == 0:
                binary_row.append(np.zeros((s,s),int))
            else:
                binary_row.append(np.array(i.to_binary()))
        binary_matrix.append(np.hstack(binary_row))
    return np.vstack(binary_matrix)

def write_PCM_as_mtx(r,s,A,B,H,pauli,i):
    non_zeros = sum(sum(H))
    with open("h{}{}.mtx".format(pauli,i),'w') as f:
        f.write("%%MatrixMarket matrix coordinate integer general\n")
        f.write("% Field: GF(2)\n")
        f.write("% ({},{}) QRC generated from\n".format(r,s))
        f.write("% A = {}\n".format(A.flatten()))
        f.write("% B = {}\n".format(B.flatten()))
        f.write("{} {} {}\n".format(len(H),len(H[0]),non_zeros))
        for i in range(len(H)):
            for j in range(len(H[0])):
                if H[i][j] == 1:
                    f.write("{} {} 1\n".format(i+1,j+1))

if __name__ == "__main__":

    if len(sys.argv) != 6:
        sys.exit("Incorrect number of arguments (expected 5)")

    r = int(sys.argv[1])
    s = int(sys.argv[2])
    abdiff = bool(sys.argv[3])
    checkdiff = bool(sys.argv[4])
    n_codes = int(sys.argv[5])

    for i in range(n_codes):
        A = matgen(r,s,checkdiff)
        if (abdiff):
            B = matgen(r,s,checkdiff)
        else:
            B = A

        A_proto = np.array([[Circulant(s,x) for x in row] for row in A])
        B_proto = np.array([[Circulant(s,x) for x in row] for row in B])
       
        HX, HZ = lifted_product(A_proto,B_proto,s)
        HX = protograph_to_binary_matrix(HX,s)
        HZ = protograph_to_binary_matrix(HZ,s)

        write_PCM_as_mtx(r,s,A,B,HX,'x',i+1)
        write_PCM_as_mtx(r,s,A,B,HZ,'z',i+1)
