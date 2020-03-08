import subprocess

def update(config):
    pass

def run(config):
    exec_all_svcs(config, 'start')

def stop(config):
    exec_all_svcs(config, 'stop')

def exec_all_svcs(config, cmd):
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

    if args.operation == 'install' or args.operation == 'update':
        print('Installing / updating')
        update(config)
    elif args.operation == 'run' or args.operation == 'start':
        print('Running')
        run(config)
    elif args.operation == 'stop':
        print('Stopping')
        stop(config)
    else:
        raise(Exception('Unknown operation'))
