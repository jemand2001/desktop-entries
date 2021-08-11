from typing import Iterable, Tuple

from configparser import ConfigParser
from os import path, listdir, environ
from sys import stderr
from enum import Flag, auto

DEFAULT_PATHS = (
    f'{environ["HOME"]}/.local/share/applications',
    '/usr/local/share/applications',
    '/usr/share/applications',
)


class Output(Flag):
    path = auto()
    name = auto()
    executable = auto()
    generic_name = auto()
    exec = executable
    generic = generic_name


def get_apps(paths: Iterable[str]) -> Iterable[Tuple[str, ConfigParser]]:
    for p in paths:
        # print(p, file=stderr)
        try:
            entries = filter(lambda s: s.endswith('.desktop'), listdir(p))
        except FileNotFoundError:
            continue
        for f in entries:
            name = path.join(p, f)
            # print(name, file=stderr)
            app = ConfigParser(interpolation=None)
            assert app.read(name)
            # print(name, *app.items())
            if 'Desktop Entry' in app and 'Exec' in app['Desktop Entry']:
                # print(name, file=stderr)
                yield name, app


def find_app(name: str, paths: Iterable[str]):
    for path, app in get_apps(paths):
        if app['Desktop Entry']['Name'].lower() == name.lower():
            return path, app


def format_entry(e: Tuple[str, ConfigParser], spec: Output, sep='\t') -> str:
    l = []
    path, app = e
    if Output.path in spec:
        l.append(path)
    if Output.name in spec:
        l.append(app['Desktop Entry']['Name'])
    if Output.generic_name in spec:
        l.append(app['Desktop Entry'].get('GenericName'))
    if Output.executable in spec:
        l.append(app['Desktop Entry'].get('Exec'))
    return sep.join(l)


def main():
    from argparse import ArgumentParser
    from contextlib import suppress
    from operator import or_
    from functools import reduce

    parser = ArgumentParser()
    parser.add_argument('-p', default=[], action='append',
                        help='Additional paths to search')
    parser.add_argument('--no-defaults', action='store_true',
                        help='If specified, do not search default paths')
    parser.add_argument(
        '-n', default=None, help='If specified, the name of the application to search')
    parser.add_argument('--output', default='name,path', help=f'comma separated list of output'
                        f' fields (any combination of ({", ".join(o.name for o in Output)}))')
    parser.add_argument('--sep', default='\t')
    args = parser.parse_args()

    paths = []
    if not args.no_defaults:
        paths.extend(DEFAULT_PATHS)
    paths.extend(args.p)

    output_options = reduce(or_, (Output[i] for i in args.output.split(',')))

    with suppress(BrokenPipeError):
        if args.n is not None:
            entry = find_app(args.n, paths)
            if entry is None:
                exit(1)
            else:
                print(format_entry(entry, output_options, args.sep))
        else:
            for e in get_apps(paths):
                print(format_entry(e, output_options, args.sep))


if __name__ == '__main__':
    main()
