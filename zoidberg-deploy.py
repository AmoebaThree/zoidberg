import argparse
import subprocess
import yaml
import os

root_dir = '/home/pi/zoidberg-deploy'


def execute_systemctl(service_name, service_config, command):
    is_system = 'system' in service_config and service_config['system']

    print('START systemctl ' + command + ' ' + service_name)

    try:
        if is_system:
            subprocess.check_call(
                ['sudo', 'systemctl', command, service_name], stderr=subprocess.STDOUT)
        else:
            subprocess.check_call(
                ['systemctl', '--user', command, service_name], stderr=subprocess.STDOUT)
        print('OK systemctl ' + command + ' ' + service_name)
    except:
        print('ERROR systemctl ' + command + ' ' + service_name)


def restart(config, services):
    for service in services:
        service_config = config['services'][service]
        execute_systemctl(service, service_config, 'restart')


def stop(config, services):
    for service in services:
        service_config = config['services'][service]
        execute_systemctl(service, service_config, 'stop')


def start(config, services):
    for service in services:
        service_config = config['services'][service]
        execute_systemctl(service, service_config, 'start')


def update(config, services):
    sources = set()
    for service in services:
        service_config = config['services'][service]
        is_system = 'system' in service_config and service_config['system']

        if is_system:
            print('Not updating ' + service + ' as it is system')
            continue

        sources.add(config['services'][service]['source'])

    for source in sources:
        try:
            print('START Updating ' + source)

            target_dir = root_dir + '/' + source
            subprocess.check_call(
                ['git', 'reset', '--hard'], stderr=subprocess.STDOUT, cwd=target_dir)
            subprocess.check_call(
                ['git', 'checkout', 'master'], stderr=subprocess.STDOUT, cwd=target_dir)
            subprocess.check_call(
                ['git', 'pull'], stderr=subprocess.STDOUT, cwd=target_dir)

            print('OK Updating ' + source)
        except Exception as e:
            print(e)
            print('ERROR Updating ' + source)


def install_prereqs():
    print('START install deps')
    try:
        subprocess.check_call(
            ['sudo', 'apt-get', 'install', 'python3', 'git', 'python3-pip', '-y'], stderr=subprocess.STDOUT)
        subprocess.check_call(
            ['sudo', 'update-alternatives', '--set', 'python', '/usr/bin/python3'], stderr=subprocess.STDOUT)
        subprocess.check_call(
            ['pip', 'install', 'pyyaml'], stderr=subprocess.STDOUT)
        print('OK install deps')
    except:
        print('ERROR install deps')


def execute_shutdown():
    subprocess.check_call(['sudo', 'shutdown', '-h', 'now'],
                          stderr=subprocess.STDOUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config YAML file')
    parser.add_argument('operation', help='Operation to execute')
    parser.add_argument('services', nargs='*',
                        help='Optional subset services to act on')
    args = parser.parse_args()

    print('Parsing configuration file "' + args.config + '"')
    config_stream = open(args.config, 'r')
    config = yaml.safe_load(config_stream)

    if args.operation == 'start':
        start(config, args.services)
    elif args.operation == 'stop':
        stop(config, args.services)
    elif args.operation == 'restart':
        restart(config, args.services)
    elif args.operation == 'update':
        update(config, args.services)
    elif args.operation == 'install-prereqs':
        install_prereqs()
    elif args.operation == 'shutdown':
        os.remove(args.config)
        execute_shutdown()

    if os.path.exists(args.config):
        os.remove(args.config)
