import subprocess
import threading
import argparse
import yaml
import random


target_root = '/home/pi/zoidberg-deploy'
target_script = target_root + '/zoidberg-deploy.py'


def get_temp_target_config():
    return target_root + '/deploy_' + str(random.randrange(100000, 999999)) + ".yaml"


def get_connection(config, host_name):
    '''Gets connection details for the specified host name'''
    host_details = config['hosts'][host_name]
    if 'user' in host_details:
        return host_details['user'] + '@' + host_details['ip']
    else:
        return host_details['ip']


def get_services_for_host(config, host, services):
    '''Helper to return which services apply to the specified host'''
    if len(services) == 0:
        services = config['services'].keys()

    found_services = []

    for service in services:
        if config['services'][service]['host'] == host:
            found_services.append(service)

    return found_services


def thread_execute_on_connection(connection, desc, commands):
    '''Helper to call one or more commands on a connection'''
    print('START ' + desc + ' ' + connection)
    try:
        subprocess.check_call(['ssh', connection] + commands,
                              stderr=subprocess.STDOUT)
        print('OK ' + desc + ' ' + connection)
    except:
        print('ERROR ' + desc + ' ' + connection)


def execute_remote_service_command(config, remote_config, hosts, services, command, description, extra_args=[]):
    '''Helper for executing remote zoidberg commands'''
    threads = []
    args = ['python', target_script, remote_config, command]

    for host in hosts:
        connection = get_connection(config, host)
        host_services = get_services_for_host(config, host, services)

        if len(host_services) == 0:
            continue

        thread = threading.Thread(
            target=thread_execute_on_connection, args=(connection, description, args + host_services + extra_args))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def start(config, remote_config, hosts, services):
    '''Start specified or all services'''
    execute_remote_service_command(
        config, remote_config, hosts, services, 'start', 'Starting services')


def stop(config, remote_config, hosts, services):
    '''Stop specified or all services'''
    execute_remote_service_command(
        config, remote_config, hosts, services, 'stop', 'Stopping services')


def restart(config, remote_config, hosts, services):
    '''Restart specified or all services'''
    execute_remote_service_command(
        config, remote_config, hosts, services, 'restart', 'Restarting services')


def status(config, remote_config, hosts, services):
    '''Get status of specified or all services'''
    execute_remote_service_command(
        config, remote_config, hosts, services, 'status', 'Getting status')


def update(config, remote_config, hosts, services, restart):
    '''Update specified or all services'''
    args = ['-r'] if restart else []
    execute_remote_service_command(
        config, remote_config, hosts, services, 'update', 'Updating services', args)


def sideload(config, remote_config, hosts, services, source, restart):
    '''Sideload a specified service with local code'''
    if len(services) != 1:
        print('ERROR Must be only one service when sideloading')
        return

    args = ['-r'] if restart else []

    if source is None:
        print('ERROR Source must be specified for sideloading')
        return

    service = next(iter(services))
    host = next(iter(hosts))
    connection = get_connection(config, host)
    sideload_dir = target_root + '/sideload-' + service

    try:
        # Empty existing sideload dir
        subprocess.check_call(['ssh', connection, 'rm', '-rf', sideload_dir],
                              stderr=subprocess.STDOUT)

        # rsync over the files to be sideloaded
        print('START syncing files to target')
        subprocess.check_call(
            ['rsync', '-a', '--exclude', '\'.*\'', source, connection + ':' + sideload_dir], stderr=subprocess.STDOUT)

        # Excute update on target
        execute_remote_service_command(
            config, remote_config, hosts, services, 'sideload', 'Sideloading ' + service, args)
    except Exception as e:
        print(e)
        print('ERROR sideload ' + service + ' to ' + connection)


def install(config, remote_config, hosts, services):
    '''Install specified or all services'''
    execute_remote_service_command(
        config, remote_config, hosts, services, 'install', 'Installing services')


def ping(config, remote_config, hosts, services):
    '''Ping'''
    execute_remote_service_command(
        config, remote_config, hosts, services, 'ping', 'Pinging')


def install_prereqs(config, remote_config, hosts):
    '''Installs zoidberg prereqs on the target hosts'''
    threads = []
    args = ['python', target_script, remote_config, 'install-prereqs']

    for host in hosts:
        connection = get_connection(config, host)

        thread = threading.Thread(
            target=thread_execute_on_connection, args=(connection, 'Installing prerequisites', args))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def shutdown(config, remote_config, hosts):
    '''Shuts down the specified hosts'''
    threads = []
    masters = set()
    args = ['python', target_script, remote_config, 'shutdown']

    for host in hosts:
        if 'master' in config['hosts'][host] and config['hosts'][host]['master']:
            # Make sure we skip masters for later
            masters.add(host)
            continue

        connection = get_connection(config, host)
        thread = threading.Thread(
            target=thread_execute_on_connection, args=(connection, 'Shutting down', args))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Sequentially shut down any masters
    for host in masters:
        connection = get_connection(config, host)
        thread_execute_on_connection(connection, 'Shutting down', args)


def thread_update_zoidberg_deploy(target, local_config, remote_config):
    '''Worker for zoidberg deploy threads'''
    print('START copy zoidberg-deploy to ' + target)
    try:
        subprocess.check_call(
            ['scp', 'zoidberg-deploy.py', target + ':' + target_script], stderr=subprocess.STDOUT)
        subprocess.check_call(
            ['scp', local_config, target + ':' + remote_config], stderr=subprocess.STDOUT)
        subprocess.check_call(['ssh', target, 'chmod', '+x', target_script],
                              stderr=subprocess.STDOUT)
        print('OK copy zoidberg-deploy to ' + target)
    except Exception as e:
        print(e)
        print('ERROR copy zoidberg-deploy to ' + target)


def update_zoidberg_deploy(config, hosts, local_config, remote_config):
    '''Updates zoidberg deploy script on specified hosts'''
    threads = []

    for host in hosts:
        connection = get_connection(config, host)
        thread = threading.Thread(
            target=thread_update_zoidberg_deploy, args=(connection, local_config, remote_config))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def sanitise_services(config, input_services):
    '''Filters the input services to be a sane list'''
    services = set()

    if len(input_services) == 0:
        return services

    for service in input_services:
        if service in config['services']:
            services.add(service)
        else:
            print('Ignoring un-recognised service "' + service + '"')

    return services


def get_affected_hosts(config, services):
    '''Given some services, works out which hosts in the config need work executing'''
    hosts = set()

    if len(services) == 0:
        services = config['services'].keys()

    for service in services:
        host = config['services'][service]['host']
        if host in config['hosts']:
            hosts.add(host)
        else:
            print('Ignoring unknown host "' + host + '"')

    return hosts


if __name__ == '__main__':
    print('(V) (°,,,,°) (V)')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to config YAML file')
    parser.add_argument('operation', help='Operation to execute')
    parser.add_argument('services', nargs='*',
                        help='Optional subset services to act on')
    parser.add_argument(
        '--source', nargs='?', help='Sideload: Source path for sideload operation', type=str, default=None)
    parser.add_argument("-r", "--restart", action="store_true",
                        help="Update, Sideload: Also restart the systemctl service after the operation")
    args = parser.parse_args()

    print('Parsing configuration file "' + args.config + '"')
    config_stream = open(args.config, 'r')
    config = yaml.safe_load(config_stream)

    services = sanitise_services(config, args.services)

    if len(args.services) > 0 and len(services) == 0:
        print('All your specified services are missing, stopping')
        exit(1)

    affected_hosts = get_affected_hosts(config, services)
    remote_config = get_temp_target_config()
    update_zoidberg_deploy(config, affected_hosts, args.config, remote_config)

    if args.operation in ['start', 'run']:
        start(config, remote_config, affected_hosts, services)
    elif args.operation == 'stop':
        stop(config, remote_config, affected_hosts, services)
    elif args.operation == 'restart':
        restart(config, remote_config, affected_hosts, services)
    elif args.operation == 'status':
        status(config, remote_config, affected_hosts, services)
    elif args.operation == 'update':
        update(config, remote_config, affected_hosts, services, args.restart)
    elif args.operation == 'sideload':
        sideload(config, remote_config, affected_hosts,
                 services, args.source, args.restart)
    elif args.operation == 'install':
        install(config, remote_config, affected_hosts, services)
    elif args.operation == 'install-prereqs':
        install_prereqs(config, remote_config, affected_hosts)
    elif args.operation == 'shutdown':
        shutdown(config, remote_config, affected_hosts)
    elif args.operation == 'ping':
        ping(config, remote_config, affected_hosts, services)
    else:
        raise(Exception('Unknown operation'))
