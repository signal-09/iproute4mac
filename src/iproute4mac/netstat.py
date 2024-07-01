import re
import subprocess

from iproute4mac.utils import *


'''
https://docs.freebsd.org/en/books/handbook/advanced-networking/#routeflags
'''
RTF_PROTO1='1'       # Protocol specific routing flag #1
RTF_PROTO2='2'       # Protocol specific routing flag #2
RTF_PROTO3='3'       # Protocol specific routing flag #3
RTF_BLACKHOLE='B'    # Just discard packets (during updates)
RTF_BROADCAST='b'    # The route represents a broadcast address
RTF_CLONING='C'      # Generate new routes on use
RTF_PRCLONING='c'    # Protocol-specified generate new routes on use
RTF_DYNAMIC='D'      # Created dynamically (by redirect)
RTF_GATEWAY='G'      # Destination requires forwarding by intermediary
RTF_HOST='H'         # Host entry (net otherwise)
RTF_IFSCOPE='I'      # Route is associated with an interface scope
RTF_IFREF='i'        # Route is holding a reference to the interface
RTF_LLINFO='L'       # Valid protocol to link address translation
RTF_MODIFIED='M'     # Modified dynamically (by redirect)
RTF_MULTICAST='m'    # The route represents a multicast address
RTF_REJECT='R'       # Host or net unreachable
RTF_ROUTER='r'       # Host is a default router
RTF_STATIC='S'       # Manually added
RTF_UP='U'           # Route usable
RTF_WASCLONED='W'    # Route was generated as a result of cloning
RTF_XRESOLVE='X'     # External daemon translates proto to link address
RTF_PROXY='Y'        # Proxying; cloned routes will not be scoped
RTF_GLOBAL='g'       # Route to a destination of the global internet (policy hint)


def dumps(routes, option):
    if option['json']:
        print(json_dumps(routes, option['pretty']))
        return

    if not routes:
        return

    for route in routes:
        print(route['dst'], end='')
        if 'gateway' in route:
            print(' via %s' % route['gateway'], end='')
        print(' dev %s' % route['dev'], end='')
        if 'protocol' in route:
            print(' proto %s' % route['protocol'], end='')
        if 'scope' in route:
            print(' scope %s' % route['scope'], end='')
        if 'prefsrc' in route:
            print(' src %s' % route['src'], end='')
        print()


class netstatRegEx:
    _ipv4 = re.compile(r'^(?P<dst>(?:default|%s))(?:/(?P<prefix>\d+))?' % (IPV4ADDR)
                       + r'\s+(?P<gateway>%s|%s|link#\d+)' % (IPV4ADDR, MACADDR))
    _ipv6 = re.compile(r'^(?P<dst>(?:default|%s))(?:/(?P<prefix>\d+))?' % (IPV6ADDR)
                       + r'\s+(?P<gateway>%s|%s|link#\d+)' % (IPV6ADDR, MACADDR))
    _route = re.compile(r'^(?P<dst>(?:default|%s|%s))(?:/(?P<prefix>\d+))?' % (IPV4ADDR, IPV6ADDR)
                        + r'\s+(?P<gateway>%s|%s|%s|link#\d+)' % (IPV4ADDR, IPV6ADDR, MACADDR)
                        + r'\s+(?P<flags>\w+)'
                        + r'\s+(?P<dev>\w+)'
                        + r'\s+(?P<expire>\S+)?')

    def __init__(self, line):
        self.ipv4 = self._ipv4.match(line)
        self.ipv6 = self._ipv6.match(line)
        self.route = self._route.match(line)


def parse(res, option):
    routes = []
    for line in iter(res.split('\n')):
        match = netstatRegEx(line)

        if match.route:
            dst, prefix, gateway, flags, dev, expire = match.route.groups()

            if (RTF_WASCLONED in flags
                and not option['show_details']):
                continue

            if dst != 'default' and match.ipv4:
                dots = dst.count('.')
                if dots < 3:
                    dst = dst + '.0' * (3 - dots)
                    if not prefix:
                        prefix = 8 * (dots + 1)
            if prefix:
                dst = '%s/%s' % (dst, prefix)
            if (RTF_LLINFO in flags
                or gateway.startswith('link#')):
                routes.append({
                    'dst': dst,
                    'dev': dev,
                    'scope': 'link',
                    'flags': flags
                })
            else:
                routes.append({
                    'dst': dst,
                    'gateway': gateway,
                    'dev': dev,
                    'flags': flags
                })
            if expire and expire != '!':
                routes[-1]['expires'] = int(expire)

    return routes


def routes(argv, option):
    if option['preferred_family'] == AF_INET6:
        address_family = 'inet6'
    elif option['preferred_family'] == AF_UNIX:
        address_family = 'unix'
    else:
        address_family = 'inet'

    cmd = subprocess.run(['netstat', '-n', '-r', '-f', address_family],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         encoding="utf-8")
    if cmd.returncode != 0:
        print(cmd.stderr)
        exit(cmd.returncode)

    routes = parse(cmd.stdout, option)
    while argv:
        opt = argv.pop(0)

#    if not option['show_details']:
#        delete_keys(links, ['linkinfo'])

    return routes
