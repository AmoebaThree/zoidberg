import subprocess

def host_update(update_hosts):
    for ip in update_hosts:
        try:
            print('Updating systemctl on ' + ip)
            subprocess.check_output(
                [   'ssh', ip,
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
        ip = config['hosts'][cfg['host']]['user'] + '@' + config['hosts'][cfg['host']]['ip']
        sym_tgt = '~/.config/systemd/user/' + svc + '.service'
        deploy_tgt = '~/zoidberg-deploy/' + cfg['source']
        branch = 'master'

        if not source in installed_sources:
            # Only install the source if it hasn't been done already
            installed_sources.add(source)
            try:
                print('Install source ' + cfg['source'] + ' on ' + ip)
                # Todo support checking if directory exists or not
                subprocess.check_output(
                    [   'ssh', ip,
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
                [   'ssh', ip,
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
        ip = config['hosts'][cfg['host']]['user'] + '@' + config['hosts'][cfg['host']]['ip']
        update_hosts.add(ip)
        deploy_tgt = '~/zoidberg-deploy/' + cfg['source']
        branch = 'master'

        if source in updated_sources:
            # Skip if done already
            continue

        updated_sources.add(source)

        try:
            print('Updating ' + cfg['source'] + ' on ' + ip)
            # Todo support checking if directory exists or not
            subprocess.check_output(
                [   'ssh', ip,
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

        ip = config['hosts'][cfg['host']]['user'] + '@' + config['hosts'][cfg['host']]['ip']

        try:
            print(cmd + ' ' + svc + ' on ' + ip)
            if is_system:
                subprocess.check_output(['ssh', ip, 'sudo', 'systemctl', cmd, svc])
            else:
                subprocess.check_output(['ssh', ip, 'systemctl', '--user', cmd, svc])
            print('OK')
        except:
            print('ERR')

if __name__ == '__main__':
    import argparse, yaml

    print('(V) (°,,,,°) (V)')

    parser = argparse.ArgumentParser()
    parser.add_argument("operation", help="Operation to execute")
    parser.add_argument("config", help="Path to config YAML file")
    args = parser.parse_args()

    print('Parsing ' + args.config)
    config_stream = open(args.config, 'r')
    config = yaml.safe_load(config_stream)

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
