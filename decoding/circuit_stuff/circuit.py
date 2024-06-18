import stim
import sys
from .code import Code


def indexToCoord(i: int, r: int, s: int):
    # coordinates are (code, ring, spoke)
    coord = (i // (r * s), (i % (r * s)) // s, (i % (r * s)) % s)
    return coord


def reset_ancillae(pauli: str, n_q: int, n_s: int, p_reset: float, p_idle: float):
    circuit = stim.Circuit()
    if pauli == "Z":
        # reset
        circuit.append("RZ", [n_q + i for i in range(n_s)])
        # bit flips on reset qubits (Z ancillae)
        circuit.append("X_ERROR", [n_q + i for i in range(n_s)], p_reset)
        # depolarising noise on idle data qubits (Z code qubits)
        circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2)], p_idle)
    elif pauli == "X":
        # reset
        circuit.append("RX", [n_q + n_s + i for i in range(n_s)])
        # phase flips on reset qubits (X ancillae)
        circuit.append("Z_ERROR", [n_q + n_s + i for i in range(n_s)], p_reset)
        # depolarising noise on idle data qubits (X code qubits)
        circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2, n_q)], p_idle)
    else:
        sys.exit("Error: Invalid Pauli '{}' passed to reset_ancillae".format(pauli))
    return circuit


def apply_CXs(
    pauli: str,
    r: int,
    s: int,
    step: int,
    n_q: int,
    n_s: int,
    checkToBits: list[list[int]],
    p_cnot: float,
):
    circuit = stim.Circuit()
    if pauli == "Z":
        rel_step = step - 1
        for i in range(n_s):
            coord = indexToCoord(i, r, s)
            support = checkToBits[i]
            if rel_step < r:
                c_t = [
                    support[(rel_step + coord[1]) % r],
                    n_q + i,
                ]  # control and target qubits
                circuit.append("CNOT", c_t)
                circuit.append("DEPOLARIZE2", c_t, p_cnot)
            else:
                c_t = [support[r + ((rel_step + coord[0]) % r)], n_q + i]
                circuit.append("CNOT", c_t)
                circuit.append("DEPOLARIZE2", c_t, p_cnot)
    elif pauli == "X":
        rel_step = (step - (r + 1)) % (2 * r + 2)
        for i in range(n_s):
            coord = indexToCoord(i, r, s)
            support = checkToBits[i]
            if rel_step < r:
                c_t = [n_q + n_s + i, support[(rel_step + coord[0]) % r]]
                circuit.append("CNOT", c_t)
                circuit.append("DEPOLARIZE2", c_t, p_cnot)
            else:
                c_t = [n_q + n_s + i, support[r + ((rel_step + coord[1]) % r)]]
                circuit.append("CNOT", c_t)
                circuit.append("DEPOLARIZE2", c_t, p_cnot)
    else:
        sys.exit("Error: Invalid Pauli '{}' passed to apply_CXs".format(pauli))
    return circuit


def measure_ancillae(
    pauli: str, n_q: int, n_s: int, detectors: int, p_meas: float, p_idle: float
):
    circuit = stim.Circuit()
    if pauli == "Z":
        # bit flips before measurement
        circuit.append("X_ERROR", [n_q + i for i in range(n_s)], p_meas)
        # measurements
        circuit.append("MZ", [n_q + i for i in range(n_s)])
        for i in range(1, n_s + 1):
            if detectors == 1:
                circuit.append(
                    "DETECTOR", [stim.target_rec(-i), stim.target_rec(-(2 * n_s + i))]
                )
        # depolarising noise on idle qubits (Z code qubits)
        circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2)], p_idle)
    elif pauli == "X":
        # phase flips before measurement
        circuit.append("Z_ERROR", [n_q + n_s + i for i in range(n_s)], p_meas)
        # measurements
        circuit.append("MX", [n_q + n_s + i for i in range(n_s)])
        for i in range(1, n_s + 1):
            if detectors == 1:
                circuit.append(
                    "DETECTOR", [stim.target_rec(-i), stim.target_rec(-(2 * n_s + i))]
                )
        # depolarising noise on idle qubits (X code qubits)
        circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2, n_q)], p_idle)
    else:
        sys.exit("Error: Invalid Pauli '{}' passed to measure_ancillae".format(pauli))
    return circuit


def first_cycle(
    pauli: str,
    r: int,
    s: int,
    n_q: int,
    n_s: int,
    checkToBitsZ: list[list[int]],
    checkToBitsX: list[list[int]],
    p_idle: float,
    p_reset: float,
    p_meas: float,
    p_cnot: float,
):
    # This one initialises qubits, does not interact X ancillae for the first r steps and does not add detectors
    circuit = stim.Circuit()
    detectorsZ = 0
    for step in range(2 * r + 2):
        # init steps
        if step == 0:
            circuit += init(pauli, n_q, n_s, p_reset)
            circuit.append("TICK")
        elif step == r:
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += reset_ancillae("X", n_q, n_s, p_reset, p_idle)
            circuit.append("TICK")
        # measure step
        elif step == (2 * r + 1):
            circuit += measure_ancillae("Z", n_q, n_s, detectorsZ, p_meas, p_idle)
            if pauli == "Z":
                for i in range(n_s):
                    # If init basis was Z then first set of Z stab measurements should all be +1
                    # so add these measurement outcomes as detectors
                    circuit.append("DETECTOR", stim.target_rec(-(i + 1)))
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
        # CX only steps
        else:
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            if step < r:  # depolarising noise on idle qubits (Z stabs not active yet)
                circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2, n_q)], p_idle)
            elif step > r:
                circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
    return circuit


def second_cycle(
    pauli: str,
    r: int,
    s: int,
    n_q: int,
    n_s: int,
    checkToBitsZ: list[list[int]],
    checkToBitsX: list[list[int]],
    p_idle: float,
    p_reset: float,
    p_meas: float,
    p_cnot: float,
):
    # This one interacts X ancillae throughout and adds Z detectors (if pauli=Z) but not X detectors
    circuit = stim.Circuit()
    detectorsX = 0
    detectorsZ = 0
    if pauli == "Z":
        detectorsZ = 1
    for step in range(2 * r + 2):
        # init steps
        if step == 0:
            circuit += reset_ancillae("Z", n_q, n_s, p_reset, p_idle)
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
        elif step == r:
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += reset_ancillae("X", n_q, n_s, p_reset, p_idle)
            circuit.append("TICK")
        # measure steps
        elif step == (2 * r + 1):
            circuit += measure_ancillae("Z", n_q, n_s, detectorsZ, p_meas, p_idle)
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
        elif step == (r - 1):
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += measure_ancillae("X", n_q, n_s, detectorsX, p_meas, p_idle)
            if pauli == "X":
                for i in range(n_s):
                    # If init basis was X then first set of X stab measurements should all be +1
                    # so add these measurement outcomes as detectors
                    circuit.append("DETECTOR", stim.target_rec(-(i + 1)))
            circuit.append("TICK")
        # CX only steps
        else:
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
    return circuit


def middle_cycles(
    pauli: str,
    cycles: int,
    r: int,
    s: int,
    n_q: int,
    n_s: int,
    checkToBitsZ: list[list[int]],
    checkToBitsX: list[list[int]],
    p_idle: float,
    p_reset: float,
    p_meas: float,
    p_cnot: float,
):
    # This is just the standard cycle with all interactions and detectors
    circuit = stim.Circuit()
    if pauli == "X":
        detectorsX = 1
        detectorsZ = 0
    elif pauli == "Z":
        detectorsX = 0
        detectorsZ = 1
    for step in range(2 * r + 2):
        # init steps
        if step == 0:
            circuit += reset_ancillae("Z", n_q, n_s, p_reset, p_idle)
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
        elif step == r:
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += reset_ancillae("X", n_q, n_s, p_reset, p_idle)
            circuit.append("TICK")
        # measure steps
        elif step == (2 * r + 1):
            circuit += measure_ancillae("Z", n_q, n_s, detectorsZ, p_meas, p_idle)
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
        elif step == (r - 1):
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += measure_ancillae("X", n_q, n_s, detectorsX, p_meas, p_idle)
            circuit.append("TICK")
        # CX only steps
        else:
            circuit += apply_CXs("Z", r, s, step, n_q, n_s, checkToBitsZ, p_cnot)
            circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
            circuit.append("TICK")
    repeated_circuit = stim.Circuit(
        """REPEAT """ + str(cycles) + """ {\n""" + str(circuit) + """\n}"""
    )
    return repeated_circuit


def last_cycle(
    pauli: str,
    r: int,
    s: int,
    n_q: int,
    n_s: int,
    checkToBitsX: list[list[int]],
    p_idle: float,
    p_meas: float,
    p_cnot: float,
):
    circuit = stim.Circuit()
    detectorsX = 0
    if pauli == "X":
        detectorsX = 1
    for step in range(r - 1):
        circuit += apply_CXs("X", r, s, step, n_q, n_s, checkToBitsX, p_cnot)
        circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2)], p_idle)
        circuit.append("TICK")
    circuit += measure_ancillae("X", n_q, n_s, detectorsX, p_meas, p_idle)
    circuit.append("DEPOLARIZE1", [i for i in range(n_q // 2)], p_idle)
    circuit.append("TICK")
    return circuit


def init(pauli: str, n_q: int, n_s: int, p_reset: float):
    circuit = stim.Circuit()
    # Initialise data qubits
    if pauli == "Z":
        circuit.append("RZ", [i for i in range(n_q)])
        circuit.append("X_ERROR", [i for i in range(n_q)], p_reset)
    elif pauli == "X":
        circuit.append("RX", [i for i in range(n_q)])
        circuit.append("Z_ERROR", [i for i in range(n_q)], p_reset)
    else:
        sys.exit("Error: Invalid Pauli '{}' passed to init".format(pauli))
    # Initialise Z stabiliser ancillae
    circuit.append("RZ", [n_q + i for i in range(n_s)])
    circuit.append("X_ERROR", [n_q + i for i in range(n_s)], p_reset)
    return circuit


def readout(
    pauli: str,
    n_q: int,
    n_s: int,
    checkToBits: list[list[int]],
    logicals: list[list[int]],
    p_meas: float,
):
    circuit = stim.Circuit()
    if pauli == "Z":
        # measure out data qubits
        circuit.append("X_ERROR", [i for i in range(n_q)], p_meas)
        circuit.append("MZ", [i for i in range(n_q)])
        # final detector layer
        for i in range(n_s):
            support = checkToBits[i]
            circuit.append(
                "DETECTOR",
                [
                    stim.target_rec(qubit - n_q) for qubit in support
                ]  # compiling final stabilisers
                + [stim.target_rec(-(n_q + 2 * n_s - i))],
            )  # comparing to previous measurement
        # logical operator measurements
        for i in range(len(logicals)):
            circuit.append(
                "OBSERVABLE_INCLUDE",
                [stim.target_rec(qubit - n_q) for qubit in logicals[i]],
                i,
            )
    elif pauli == "X":
        # measure out data qubits
        circuit.append("MX", [i for i in range(n_q)])
        circuit.append("Z_ERROR", [i for i in range(n_q)], p_meas)
        # final detector layer
        for i in range(n_s):
            support = checkToBits[i]
            circuit.append(
                "DETECTOR",
                [
                    stim.target_rec(qubit - n_q) for qubit in support
                ]  # compiling final stabilisers
                + [stim.target_rec(-(n_q + n_s - i))],
            )  # comparing to previous measurement
        # logical operator measurements
        for i in range(len(logicals)):
            circuit.append(
                "OBSERVABLE_INCLUDE",
                [stim.target_rec(qubit - n_q) for qubit in logicals[i]],
                i,
            )
    else:
        sys.exit("Error: Invalid Pauli '{}' passed to readout".format(pauli))
    circuit.append("TICK")
    return circuit


def make_full_circuit(
    code: Code,
    pauli: str,
    cycles: int,
    p_idle: float,
    p_reset: float,
    p_meas: float,
    p_cnot: float,
):
    """
    pauli is initialisation and measurement basis
    r is the code radius
    cycles is number of stabiliser measurement cycles to simulate
    p_x are probabilities of various error types
    """
    n_q = code.N
    n_s = code.N // 2
    r = code.r
    s = code.s
    circuit = stim.Circuit()
    circuit += first_cycle(
        pauli,
        r,
        s,
        n_q,
        n_s,
        code.checkToBitsZ,
        code.checkToBitsX,
        p_idle,
        p_reset,
        p_meas,
        p_cnot,
    )
    circuit += second_cycle(
        pauli,
        r,
        s,
        n_q,
        n_s,
        code.checkToBitsZ,
        code.checkToBitsX,
        p_idle,
        p_reset,
        p_meas,
        p_cnot,
    )
    if cycles > 1:
        circuit += middle_cycles(
            pauli,
            cycles - 2,
            r,
            s,
            n_q,
            n_s,
            code.checkToBitsZ,
            code.checkToBitsX,
            p_idle,
            p_reset,
            p_meas,
            p_cnot,
        )
    circuit += last_cycle(
        pauli, r, s, n_q, n_s, code.checkToBitsX, p_idle, p_meas, p_cnot
    )
    if pauli == "Z":
        circuit += readout("Z", n_q, n_s, code.checkToBitsZ, code.logicalsZ, p_meas)
    elif pauli == "X":
        circuit += readout("X", n_q, n_s, code.checkToBitsX, code.logicalsX, p_meas)
    else:
        sys.exit("Error: Invalid Pauli '{}' passed to make_full_circuit".format(pauli))
    return circuit
