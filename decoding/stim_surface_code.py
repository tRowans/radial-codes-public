import numpy as np
import sinter
import stim
from matplotlib import pyplot as plt


def generate_example_tasks():
    for p in [0.0015, 0.002, 0.003, 0.004]:
        for d in [15]:
            sc_circuit = stim.Circuit.generated(
                rounds=3 * d,
                distance=d,
                after_clifford_depolarization=p,
                after_reset_flip_probability=p,
                before_measure_flip_probability=p,
                before_round_data_depolarization=p,
                code_task=f"surface_code:rotated_memory_z",
            )
            yield sinter.Task(
                circuit=sc_circuit,
                json_metadata={
                    "p": p,
                    "d": d,
                    "rounds": 3 * d,
                },
            )


def main():

    samples = sinter.collect(
        num_workers=7,
        max_shots=100_000_000,
        max_errors=100,
        tasks=generate_example_tasks(),
        decoders=["pymatching"],
        print_progress=True,
        save_resume_filepath=f"surface_code_comparisons.csv",
    )


if __name__ == "__main__":
    main()
