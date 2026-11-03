"""Plan independent bounded sync jobs without changing configured package order."""
import argparse
import json

from .coverage_validation import partition_packages
from .sync import read_config


def plan_batches(config, selected=None):
    packages = list(dict.fromkeys(package for package, _ in read_config(config)))
    if selected and selected.strip():
        requested = [package.strip() for package in selected.split(',')]
        if (len(requested) != len(set(requested)) or any(package not in packages for package in requested)):
            raise ValueError('Unknown or duplicate selected package')
        packages = [package for package in packages if package in requested]
    count = min(8, len(packages))
    return {'include': [{'batch': i, 'packages': ','.join(partition_packages(packages, i, count))}
                        for i in range(count)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='apps.json')
    parser.add_argument('--packages', default='')
    args = parser.parse_args()
    print(json.dumps(plan_batches(args.config, args.packages), separators=(',', ':')))


if __name__ == '__main__':
    main()
