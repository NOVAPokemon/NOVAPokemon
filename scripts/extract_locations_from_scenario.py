import json
import os
import sys

SCENARIOS_DIR = os.path.expanduser('~/ced-scenarios')
NOVAPOKEMON_DIR = os.path.expanduser('~/go/src/github.com/NOVAPokemon')


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print("Usage: python3 extract_locations_from_scenario.py <scenario1>")
        exit(1)

    scenario_name = args[0]

    with open(f'{SCENARIOS_DIR}/{scenario_name}', 'r') as f:
        scenario = json.load(f)

    locations = scenario['locations']

    new_locations = {}
    for dummy_name, location in locations.items():
        num = str(int(dummy_name.split("dummy")[1]) - 1)
        new_locations[num] = location

    new_locations_path = f'{NOVAPOKEMON_DIR}/locations.json'
    with open(new_locations_path, 'w') as f:
        json.dump(new_locations, f)

    print(f'Wrote locations to {new_locations_path}')


if __name__ == '__main__':
    main()
