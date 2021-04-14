import sys
import os


def main():
    args = sys.argv[1:]

    num_args = 1
    if len(args) != num_args:
        print("Usage: python3 get_experiment_min_timestamp.py <experiment_dir>")
        exit(1)

    experiment_dir = args[0]

    min_timestamp = -1.
    stats_path = f'{experiment_dir}/stats'
    for file in os.listdir(stats_path):
        read_first_timestamp = False
        first_timestamp = 0
        with open(os.path.join(stats_path, file)) as f:
            while not read_first_timestamp:
                try:
                    first_timestamp = float(f.readline().strip().split(';')[0])
                    read_first_timestamp = True
                    if first_timestamp < min_timestamp or min_timestamp == -1:
                        min_timestamp = first_timestamp
                except ValueError:
                    continue

    print(min_timestamp)


if __name__ == '__main__':
    main()
