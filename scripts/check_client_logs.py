import sys
import os


def main():
    args = sys.argv[1:]

    if len(args) != 1:
        print('Usage: python3 check_client_logs.py <client_logs_folder>')
        exit(1)

    client_logs_folder = os.path.expanduser(args[0])

    for subfolder in os.listdir(client_logs_folder):
        subfolder_path = os.path.join(client_logs_folder, subfolder)
        for log in os.listdir(subfolder_path):
            ok = False
            with open(os.path.join(subfolder_path, log)) as f:
                for line in f.readlines():
                    if 'Finishing client...' in line:
                        ok = True
            if not ok:
                print(f'{subfolder}/{log} did not finish properly')


if __name__ == '__main__':
    main()
