import subprocess

def install(config):
    for svc, cfg in config['services'].items():
        is_system = 'system' in cfg.keys() and cfg['system']

        if is_system:
            # Don't try to install systems
            continue

        if not 'source' in cfg.keys():
            print('Service ' + svc + ' missing source')
            continue

        ip = config['hosts'][cfg['host']]['user'] + '@' + config['hosts'][cfg['host']]['ip']
        sym_tgt = '~/.config/systemd/user/' + svc + '.service'
        deploy_tgt = '~/zoidberg-deploy/' + svc
        branch = 'master'

        try:
            print('Trying to install ' + svc + ' on ' + ip + ': ', end = '')
            # Todo support checking if directory exists or not
            subprocess.check_output(
                [   'ssh', ip,
                    'rm', '-rf', deploy_tgt, '&&',
                    'rm', '-f', sym_tgt, '&&',
                    'mkdir', '-p', deploy_tgt, '&&', 
                    'cd', deploy_tgt, '&&',
                    'git', 'clone', cfg['source'], '.', '&&',
                    'git', 'checkout', branch, '&&',
                    'ln', '-s', deploy_tgt + '/' + svc + '.service', sym_tgt])
            print('OK')
        except:
            print('ERR')

def update(config):
    for svc, cfg in config['services'].items():
        is_system = 'system' in cfg.keys() and cfg['system']

        if is_system:
            # Don't try to update systems
            continue

        if not 'source' in cfg.keys():
            print('Service ' + svc + ' missing source')
            continue

        ip = config['hosts'][cfg['host']]['user'] + '@' + config['hosts'][cfg['host']]['ip']
        deploy_tgt = '~/zoidberg-deploy/' + svc
        branch = 'master'

        try:
            print('Trying to update ' + svc + ' on ' + ip + ': ', end = '')
            # Todo support checking if directory exists or not
            subprocess.check_output(
                [   'ssh', ip,
                    'cd', deploy_tgt, '&&',
                    'git', 'pull'])
            print('OK')
        except:
            print('ERR')

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
            print('Trying to ' + cmd + ' ' + svc + ' on ' + ip + ': ', end = '')
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
        print('Running')
        run(config)
    elif args.operation == 'stop':
        print('Stopping')
        stop(config)
    elif args.operation == 'restart':
        print('Restarting')
        restart(config)
    else:
        raise(Exception('Unknown operation'))
