import numpy as np
import random
import sys

def difference_checker(newrow,A,r,s):
    if r == 2:
        return True
    for row in A:
        difference = newrow-row % s
        for element in difference:
            if element % 2 != 0:        #get all entries even
                element = s - element
        for element in difference:
            if element != 0:
                count = 0
                for i in difference/element:
                    count += (int(i) == i)
                if count == len(difference)-1:
                    return False
    return True

def rank_checker(newrow,A):
    trial = np.vstack((A,newrow))
    if np.linalg.matrix_rank(trial) != np.linalg.matrix_rank(A)+1:
        return False
    else:
        return True

def sum_checker_2(newrow,A,r,s):
    trial = np.vstack((A,newrow))
    for i in range(len(trial)-1):
        for j in range(r):
            for k in range(j+1,r):
                if (trial[i][j] 
                    - trial[i][k] 
                    - trial[-1][j] 
                    + trial[-1][k]) % s == 0:
                    return False
    return True

def sum_checker_3(newrow,A,r,s):
    trial = np.vstack((A,newrow))
    for row1 in range(len(trial)-2):
        for row2 in range(row1+1,len(trial)-1):
            for row3 in range(row2+1,len(trial)):
                for col1 in range(r):
                    for col2 in range(r):
                        for col3 in range(r):
                            if (col2 == col3):
                                continue
                            if (trial[row1][col1] 
                                - trial[row1][col2] 
                                - trial[row2][col1]
                                + trial[row2][col3]
                                + trial[row3][col2]
                                - trial[row3][col3]) % s == 0:
                                return False 
    return True

def matgen(r,s,checkdiff=False):
    mat_attempts = 0
    while mat_attempts < 1000:
        A = []
        firstrow = np.array([random.randrange(s) for i in range(r)])
        A.append(firstrow)
        for row_index in range(1,r):
            validrow = False
            row_attempts = 0
            while not validrow and row_attempts < 1000:
                row_attempts += 1
                newrow = np.array([random.randrange(s) for i in range(r)])
                if (checkdiff):
                    validrow = (difference_checker(newrow,A,r,s) 
                                and rank_checker(newrow,A) 
                                and sum_checker_2(newrow,A,r,s))
                else:
                    validrow = (rank_checker(newrow,A) 
                                and sum_checker_2(newrow,A,r,s))
            if row_attempts == 1000:
                break
            A.append(newrow)
        else:
            return np.array(A)
        mat_attempts += 1
    sys.exit("Failed to generate matrix in 1000 attempts")

if __name__ == "__main__":

    if len(sys.argv) != 3:
        sys.exit("Incorrect number of arguments (expected 2)")

    r = int(sys.argv[1])
    s = int(sys.argv[2])

    print(matgen(r,s))
