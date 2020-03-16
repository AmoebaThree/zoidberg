import argparse
import subprocess
import yaml
import os

root_dir = '/home/pi/zoidberg-deploy'


def update_systemctl():
    try:
        print('START update systemctl')
        subprocess.check_call(
            ['systemctl', '--user', 'daemon-reload'], stderr=subprocess.STDOUT)
        print('OK update systemctl')
    except:
        print('ERROR update systemctl')


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


def status(config, services):
    for service in services:
        service_config = config['services'][service]
        execute_systemctl(service, service_config, 'status')


def stop(config, services):
    for service in services:
        service_config = config['services'][service]
        execute_systemctl(service, service_config, 'stop')


def start(config, services):
    for service in services:
        service_config = config['services'][service]
        execute_systemctl(service, service_config, 'start')


def execute_scripts(source_prereqs, services, script_name):
    script_key = script_name
    script_root_key = script_name + '_root'

    for source, source_prereq in source_prereqs.items():
        script = []
        script_root = []

        if script_key in source_prereq:
            script.extend(source_prereq[script_key])
        if script_root_key in source_prereq:
            script_root.extend(source_prereq[script_root_key])
        if 'services' in source_prereq:
            for service_config_name, service_config in source_prereq['services'].items():
                if service_config_name not in services:
                    continue

                if script_key in service_config:
                    script.extend(service_config[script_key])
                if script_root_key in service_config:
                    script_root.extend(service_config[script_root_key])

        if len(script) > 0 or len(script_root) > 0:
            target_dir = root_dir + '/' + source
            try:
                print('START ' + script_name + ' scripts for ' + source)

                for script_command in script:
                    subprocess.check_call(
                        script_command.split(), stderr=subprocess.STDOUT, cwd=target_dir)

                for script_command in script_root:
                    subprocess.check_call(
                        ['sudo'] + script_command.split(), stderr=subprocess.STDOUT, cwd=target_dir)

                print('OK ' + script_name + ' scripts for ' + source)
            except:
                print('ERROR ' + script_name + ' scripts for ' + source)


def update(config, services):
    sources = set()
    source_prereqs = dict()

    for service in services:
        service_config = config['services'][service]
        is_system = 'system' in service_config and service_config['system']

        if is_system:
            print('Not updating ' + service + ' as it is system')
            continue

        if not 'source' in service_config:
            print('ERROR Service ' + service + ' missing source')
            continue

        sources.add(config['services'][service]['source'])

    for source in sources:
        try:
            print('START Updating ' + source)

            source_config = config['sources'][source]
            target_dir = root_dir + '/' + source
            branch = 'master'
            if 'branch' in source_config:
                branch = source_config['branch']

            subprocess.check_call(
                ['git', 'reset', '--hard'], stderr=subprocess.STDOUT, cwd=target_dir)
            subprocess.check_call(
                ['git', 'checkout', branch], stderr=subprocess.STDOUT, cwd=target_dir)
            subprocess.check_call(
                ['git', 'pull'], stderr=subprocess.STDOUT, cwd=target_dir)

            print('OK Updating ' + source)
        except:
            print('ERROR Updating ' + source)

        source_config_file = target_dir + '/prereqs.yaml'
        if os.path.exists(source_config_file):
            source_config_stream = open(source_config_file, 'r')
            source_prereqs[source] = yaml.safe_load(source_config_stream)

    execute_scripts(source_prereqs, services, 'update')
    update_systemctl()


def install(config, services):
    sources = set()
    source_prereqs = dict()
    apt = set()
    pip = set()

    for service in services:
        service_config = config['services'][service]
        is_system = 'system' in service_config and service_config['system']

        if is_system:
            if 'apt' in service_config:
                apt.update(service_config['apt'])
            if 'pip' in service_config:
                pip.update(service_config['pip'])
            continue

        if not 'source' in service_config:
            print('ERROR Service ' + service + ' missing source')
            continue

        sources.add(config['services'][service]['source'])

    for source in sources:
        try:
            print('START Installing ' + source)

            source_config = config['sources'][source]
            target_dir = root_dir + '/' + source
            source_uri = source_config['source']
            branch = 'master'
            if 'branch' in source_config:
                branch = source_config['branch']

            subprocess.check_call(
                ['rm', '-rf', target_dir], stderr=subprocess.STDOUT)
            subprocess.check_call(
                ['mkdir', '-p', target_dir], stderr=subprocess.STDOUT)
            subprocess.check_call(
                ['git', 'clone', source_uri, '.'], stderr=subprocess.STDOUT, cwd=target_dir)
            subprocess.check_call(
                ['git', 'checkout', branch], stderr=subprocess.STDOUT, cwd=target_dir)

            print('OK Installing ' + source)
        except:
            print('ERROR Installing ' + source)

        source_config_file = target_dir + '/prereqs.yaml'
        if os.path.exists(source_config_file):
            source_config_stream = open(source_config_file, 'r')
            source_prereqs[source] = yaml.safe_load(source_config_stream)

    for service in services:
        service_config = config['services'][service]
        is_system = 'system' in service_config and service_config['system']

        if is_system:
            continue

        try:
            print('START Symlink ' + service)
            target_dir = root_dir + '/' + service_config['source']
            symlink_target = '/home/pi/.config/systemd/user/' + service + '.service'
            subprocess.check_call(
                ['rm', '-f', symlink_target], stderr=subprocess.STDOUT)
            subprocess.check_call(
                ['ln', '-s', target_dir + '/' + service + '.service', symlink_target], stderr=subprocess.STDOUT)
            print('OK Symlink ' + service)
        except:
            print('ERROR Symlink ' + service)

    for _, source_prereq in source_prereqs.items():
        if 'apt' in source_prereq:
            apt.update(source_prereq['apt'])

        if 'pip' in source_prereq:
            pip.update(source_prereq['pip'])

        if 'services' in source_prereq:
            for service_config_name, service_config in source_prereq['services'].items():
                if service_config_name not in services:
                    continue

                if 'apt' in service_config:
                    apt.update(service_config['apt'])

                if 'pip' in service_config:
                    pip.update(service_config['pip'])

    if len(apt) > 0:
        try:
            print('START apt package install: ' + ', '.join(apt))
            subprocess.check_call(
                ['sudo', 'apt-get', 'install'] + list(apt), stderr=subprocess.STDOUT)
            print('OK apt package install')
        except:
            print('ERROR apt package install')

    if len(pip) > 0:
        try:
            print('START pip package install: ' + ', '.join(pip))
            subprocess.check_call(['pip', 'install'] + list(pip),
                                  stderr=subprocess.STDOUT)
            print('OK pip package install')
        except:
            print('ERROR pip package install')

    execute_scripts(source_prereqs, services, 'setup')
    update_systemctl()


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
    elif args.operation == 'status':
        status(config, args.services)
    elif args.operation == 'update':
        update(config, args.services)
    elif args.operation == 'install':
        install(config, args.services)
    elif args.operation == 'install-prereqs':
        install_prereqs()
    elif args.operation == 'shutdown':
        os.remove(args.config)
        execute_shutdown()
    elif args.operation == 'ping':
        print('Pong')

    if os.path.exists(args.config):
        os.remove(args.config)
