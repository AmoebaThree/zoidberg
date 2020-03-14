import argparse
import subprocess

def execute_shutdown():
    subprocess.check_output(['sudo', 'shutdown', '-h', 'now'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', help='Operation to execute')
    args = parser.parse_args()

    if args.operation == 'shutdown':
        execute_shutdown()
    else:
        raise(Exception('Unknown operation'))