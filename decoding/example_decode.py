import numpy as np
import sinter
import stim
import os
from datetime import date
from typing import List, Union
from ckt_noise import SinterDecoder_BPOSD_OWD
import circuit_stuff as cs

CODES_PATH = "PCMs/"


def load_code(code: str, r: int, s: int):
    path = CODES_PATH + code + "/"
    hx = np.loadtxt(path + "hx.csv", delimiter=",", dtype=int)
    hz = np.loadtxt(path + "hz.csv", delimiter=",", dtype=int)
    lx = np.loadtxt(path + "lx.csv", delimiter=",", dtype=int)
    lz = np.loadtxt(path + "lz.csv", delimiter=",", dtype=int)
    return cs.Code(r, s, hx, hz, lx, lz)


def get_radial_code(code_dist: int):
    # [[90, 8, 10]]

    if code_dist == 10:
        code_name = "90_8_10"
        r = 3
        s = 5
        code = load_code(code_name, r, s)

    if code_dist == 20:
        code_name = "352_18_20"
        r = 4
        s = 11
        code = load_code(code_name, r, s)

    return code, code_name


if __name__ == "__main__":
    code_dist = 10
    rounds = 12
    ps = 0.001
    window = 1
    commit = 1
    pauli = "Z"

    code, code_name = get_radial_code(code_dist)
    circuit = cs.make_full_circuit(
        code,
        pauli,
        rounds,
        p_idle=ps,
        p_reset=ps,
        p_meas=ps,
        p_cnot=ps,
    )
    dem = circuit.detector_error_model()

    if pauli == "X":
        n_checks = code.nX
    elif pauli == "Z":
        n_checks = code.nZ

    decoders = {}
    default_decoder_args = {
        "max_iter": 100,
        "bp_method": "ms",
        "osd_method": "osd_0",
        # "ms_scaling_factor": .625,
        "schedule": "parallel",
    }
    tasks = []
    decodings = (rounds - window + 1) // commit + 1
    decoders[f"bposd_owd_{n_checks}_{pauli}"] = SinterDecoder_BPOSD_OWD(
        decodings=decodings,
        window=window,
        commit=commit,
        num_checks=int(n_checks),
        decoder_config=default_decoder_args,
    )
    decoder_name = f"bposd_owd_{n_checks}_{pauli}"

    tasks.append(
        sinter.Task(
            circuit=circuit,
            decoder=decoder_name,
            detector_error_model=dem,
            json_metadata={
                "code_name": code_name,
                "rounds": rounds,
                "p": ps,
                "window": window,
                "commit": commit,
                "decodings": decodings,
                "pauli": pauli,
                "decoder": "bposd",
                "decoder_args": decoders[decoder_name].decoder_kwargs,
                "distance": code_dist,
            },
        )
    )

    samples = sinter.collect(
        num_workers=4,
        max_shots=10_000,
        max_errors=100,
        tasks=tasks,
        custom_decoders=decoders,
        save_resume_filepath="example_decode.csv",
    )
