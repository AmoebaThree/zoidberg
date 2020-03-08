if __name__ == '__main__':
    import argparse
    import yaml

    print('(V) (°,,,,°) (V)')

    parser = argparse.ArgumentParser()
    parser.add_argument("operation", help="Operation to execute")
    parser.add_argument("config", help="Path to config YAML file")
    args = parser.parse_args()

    config = yaml.safe_load(args.config)

    if args.operation == 'install' or args.operation == 'update':
        pass
    elif args.operation == 'run':
        pass
    else:
        raise(Exception('Unknown operation'))
