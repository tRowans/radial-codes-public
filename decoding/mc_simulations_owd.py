import numpy as np
import sinter
import stim
import os
from datetime import date
from typing import List, Union
from ckt_noise import SinterDecoder_BPOSD_OWD
import circuit_stuff as cs

CODES_PATH = "radial-codes-public/PCMs/"


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


def generate_tasks_and_decoders(
    ps: float,
    ds: float,
    rounds: int,
    windows: int,
    commits: int,
    decoder: str,
    decoder_args: dict,
    pauli: str,
):

    pauli = pauli.upper()

    decoders = {}
    tasks = []

    code, code_name = get_radial_code(ds)
    circuit = cs.make_full_circuit(code, pauli, rounds, ps, ps, ps, ps)
    dem = circuit.detector_error_model()

    if pauli == "X":
        n_checks = code.nX
    elif pauli == "Z":
        n_checks = code.nZ

    decodings = (rounds - windows + 1) // commits + 1

    if decoder == "bposd":
        decoders[f"bposd_owd_{n_checks}_{pauli}"] = SinterDecoder_BPOSD_OWD(
            decodings=decodings,
            window=windows,
            commit=commits,
            num_checks=int(n_checks),
            decoder_kwargs=decoder_args,
        )
        decoder_name = f"bposd_owd_{n_checks}_{pauli}"

    else:
        raise ValueError(f"Unknown decoder: {decoder}")

    tasks.append(
        sinter.Task(
            circuit=circuit,
            decoder=decoder_name,
            detector_error_model=dem,
            json_metadata={
                "code_name": code_name,
                "rounds": rounds,
                "p": ps,
                "window": windows,
                "commit": commits,
                "decodings": decodings,
                "pauli": pauli,
                "decoder_args": decoder_args,
                "decoder": decoder,
                "distance": ds,
            },
        )
    )

    return tasks, decoders


def run_ec_simulation(
    ps: float,
    ds: float,
    rounds: int,
    windows: int,
    commits: int,
    decoder: str,
    decoder_args: dict,
    pauli: str,
    output_path: str,
    max_shots: int = 50_000,
    max_errors: int = 500,
    idx: int = 0,
):
    num_workers = os.cpu_count() // 2  # Hyperthreading
    print("Number of workers: ", num_workers)

    tasks, decoders = generate_tasks_and_decoders(
        ps, ds, rounds, windows, commits, decoder, decoder_args, pauli
    )

    samples = sinter.collect(
        num_workers=num_workers,
        max_shots=max_shots,
        max_errors=max_errors,
        tasks=tasks,
        custom_decoders=decoders,
        save_resume_filepath=output_path,
    )

    # Print samples as CSV data.
    print(sinter.CSV_HEADER)
    for sample in samples:
        print(sample.to_csv_line())

    return


if __name__ == "__main__":
    pass
