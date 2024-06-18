import os
import json
import typer
from mc_simulations_owd import run_ec_simulation

def main(input_file: str, start: int, end: int):
    with open(input_file, "r") as file:
        params = json.load(file)
        for i in range(start, end + 1):
            print(f"\nParams = \n{params[i]}")
            run_ec_simulation(**params[i], idx=i)


if __name__ == "__main__":
    typer.run(main)