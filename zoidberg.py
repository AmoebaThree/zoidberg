import subprocess
import threading
import argparse
import yaml


def host_update(update_hosts):
    for ip in update_hosts:
        try:
            print('Updating systemctl on ' + ip)
            subprocess.check_output(
                ['ssh', ip,
                    'systemctl', '--user', 'daemon-reload'])
            print('OK')
        except:
            print('ERR')


def install(config):

    update_hosts = set()
    installed_sources = set()

    for svc, cfg in config['services'].items():
        is_system = 'system' in cfg.keys() and cfg['system']

        if is_system:
            # Don't try to install systems
            continue

        if not 'source' in cfg.keys() or cfg['source'] not in config['sources'].keys():
            print('Service ' + svc + ' missing source')
            continue

        source = config['sources'][cfg['source']]['source']
        ip = config['hosts'][cfg['host']]['user'] + \
            '@' + config['hosts'][cfg['host']]['ip']
        sym_tgt = '~/.config/systemd/user/' + svc + '.service'
        deploy_tgt = '~/zoidberg-deploy/' + cfg['source']
        branch = 'master'

        if not source + ip in installed_sources:
            # Only install the source if it hasn't been done already
            installed_sources.add(source + ip)
            try:
                print('Install source ' + cfg['source'] + ' on ' + ip)
                # Todo support checking if directory exists or not
                subprocess.check_output(
                    ['ssh', ip,
                        'rm', '-rf', deploy_tgt, '&&',
                        'mkdir', '-p', deploy_tgt, '&&',
                        'cd', deploy_tgt, '&&',
                        'git', 'clone', source, '.', '&&',
                        'git', 'checkout', branch])
                print('OK')
            except:
                print('ERR')

        # Now we can make the service
        try:
            print('Install service ' + svc + ' on ' + ip)
            update_hosts.add(ip)
            subprocess.check_output(
                ['ssh', ip,
                    'rm', '-f', sym_tgt, '&&',
                    'ln', '-s', deploy_tgt + '/' + svc + '.service', sym_tgt])
            print('OK')
        except:
            print('ERR')

    host_update(update_hosts)


def update(config):

    update_hosts = set()
    updated_sources = set()

    for svc, cfg in config['services'].items():
        is_system = 'system' in cfg.keys() and cfg['system']

        if is_system:
            # Don't try to update systems
            continue

        if not 'source' in cfg.keys() or cfg['source'] not in config['sources'].keys():
            print('Service ' + svc + ' missing source')
            continue

        source = config['sources'][cfg['source']]['source']
        ip = config['hosts'][cfg['host']]['user'] + \
            '@' + config['hosts'][cfg['host']]['ip']
        update_hosts.add(ip)
        deploy_tgt = '~/zoidberg-deploy/' + cfg['source']
        branch = 'master'

        if source + ip in updated_sources:
            # Skip if done already
            continue

        updated_sources.add(source + ip)

        try:
            print('Updating ' + cfg['source'] + ' on ' + ip)
            # Todo support checking if directory exists or not
            subprocess.check_output(
                ['ssh', ip,
                    'cd', deploy_tgt, '&&',
                    'git', 'reset', '--hard', '&&',
                    'git', 'pull'])
            print('OK')
        except:
            print('ERR')

    host_update(update_hosts)


def run(config):
    systemctl_all(config, 'start')


def stop(config):
    systemctl_all(config, 'stop')


def restart(config):
    systemctl_all(config, 'restart')


def systemctl_all(config, cmd):
    for svc, cfg in config['services'].items():
        is_system = 'system' in cfg.keys() and cfg['system']

        if not 'host' in cfg.keys() or not cfg['host'] in config['hosts'].keys():
            print('Service ' + svc + ' missing host')
            continue

        ip = config['hosts'][cfg['host']]['user'] + \
            '@' + config['hosts'][cfg['host']]['ip']

        try:
            print(cmd + ' ' + svc + ' on ' + ip)
            if is_system:
                subprocess.check_output(
                    ['ssh', ip, 'sudo', 'systemctl', cmd, svc])
            else:
                subprocess.check_output(
                    ['ssh', ip, 'systemctl', '--user', cmd, svc])
            print('OK')
        except:
            print('ERR')


target_script = '~/zoidberg-deploy/zoidberg-deploy.py'


def get_connection(config, host_name):
    '''Gets connection details for the specified host name'''
    host_details = config['hosts'][host_name]
    if 'user' in host_details:
        return host_details['user'] + '@' + host_details['ip']
    else:
        return host_details['ip']


def thread_shutdown(target):
    '''Worker for shutting down targets'''
    print('Shutting down ' + target)
    try:
        subprocess.check_output(
            ['ssh', target, 'python', target_script, 'shutdown'])
        print('Successfully shut down ' + target)
    except:
        print('ERROR shutting down ' + target)


def shutdown(config, hosts):
    '''Shuts down the specified hosts'''
    threads = []

    masters = set()

    for host in hosts:
        if 'master' in config['hosts'][host] and config['hosts'][host]['master']:
            # Make sure we skip masters for later
            masters.add(host)
            continue

        connection = get_connection(config, host)
        thread = threading.Thread(target=thread_shutdown, args=(connection,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Sequentially shut down any masters
    for host in masters:
        connection = get_connection(config, host)
        thread_shutdown(connection)


def thread_update_zoidberg_deploy(target):
    '''Worker for zoidberg deploy threads'''
    print('Updating zoidberg-deploy on ' + target)
    try:
        subprocess.check_output(
            ['scp', 'zoidberg-deploy.py', target + ':' + target_script])
        subprocess.check_output(['ssh', target, 'chmod', '+x', target_script])
        print('Updated zoidberg-deploy on ' + target)
    except:
        print('ERROR updating zoidberg-deploy on ' + target)


def update_zoidberg_deploy(config, hosts):
    '''Updates zoidberg deploy script on specified hosts'''
    threads = []

    for host in hosts:
        connection = get_connection(config, host)
        thread = threading.Thread(
            target=thread_update_zoidberg_deploy, args=(connection,))
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
    args = parser.parse_args()

    print('Parsing configuration file "' + args.config + '"')
    config_stream = open(args.config, 'r')
    config = yaml.safe_load(config_stream)

    services = sanitise_services(config, args.services)

    if len(args.services) > 0 and len(services) == 0:
        print('All your specified services are missing, stopping')
        exit(1)

    affected_hosts = get_affected_hosts(config, services)
    update_zoidberg_deploy(config, affected_hosts)

    if args.operation == 'shutdown':
        shutdown(config, affected_hosts)
    else:
        raise(Exception('Unknown operation'))

    exit(0)
    if args.operation == 'install':
        print('Installing')
        install(config)
    elif args.operation == 'update':
        print('Updating')
        update(config)
    elif args.operation == 'run' or args.operation == 'start':
        print('Starting')
        run(config)
    elif args.operation == 'stop':
        print('Stopping')
        stop(config)
    elif args.operation == 'restart':
        print('Restarting')
        restart(config)
    else:
        raise(Exception('Unknown operation'))
