import re
import subprocess

from iproute4mac.utils import *


def json_dumps(data, pretty=False):
    if pretty:
        return json.dumps(data, cls=IpRouteJSON, indent=4)
    else:
        return json.dumps(data, separators=(',', ':'))


def text_dumps(data):
    lines = []
    for line in data:
        dev = line['ifname'] + '@' + line['link'] if 'link' in line else line['ifname']
        desc = 'mtu {}'.format(line['mtu'])
        if 'master' in line:
            desc = '{} master {}'.format(desc, line['master'])
        desc = '{} state {}'.format(desc, line['operstate'])
        lines.append('%d: %s: <%s> %s' % (
            line['ifindex'], dev, ','.join(line['flags']), desc
        ))
        lines.append('    link/' + line['link_type']
                     + ((' ' + line['address']) if 'address' in line else '')
                     + ((' brd ' + line['broadcast']) if 'broadcast' in line else ''))
        if 'linkinfo' in line and 'info_kind' in line['linkinfo']:
            i = line['linkinfo']
            if i['info_kind'] == 'vlan':
                lines.append('    %s protocol %s id %d' %
                             (i['info_kind'], i['info_data']['protocol'], i['info_data']['id']))
            elif i['info_kind'] == 'bridge':
                lines.append('    bridge ' + ' '.join(['%s %s' % (k, v) for k, v in i['info_data'].items()]))
        for a in line.get('addr_info', []):
            address = '%s peer %s' % (a['local'], a['address']) if 'address' in a else a['local']
            lines.append('    %s %s/%d' % (a['family'], address, a['prefixlen'])
                         + ((' brd ' + a['broadcast']) if 'broadcast' in a else ''))
    return '\n'.join(lines)


def dumps(data, option):
    if option['json']:
        print(json_dumps(data, option['pretty']))
    elif data:
        print(text_dumps(data))


class ifconfigRegEx:
    _header = re.compile(r'^(?P<ifname>\w+):'
                         r' flags=\w+<(?P<flags>.*)>'
                         r' mtu (?P<mtu>\d+)'
                         r' index (?P<ifindex>\d+)')
    _eflags = re.compile(r'^\s+eflags=\w+<(?P<eflags>.*)>')
    _ether = re.compile(r'^\s+ether ((?:[0-9a-fA-F]{2}:?){6})')
    _inet = re.compile(r'^\s+inet (?P<local>\d+\.\d+\.\d+\.\d+)'
                       r'(?: --> (?P<address>\d+\.\d+\.\d+\.\d+))?'
                       r' netmask (?P<netmask>0x[0-9a-f]{8})'
                       r'(?: broadcast (?P<broadcast>\d+\.\d+\.\d+\.\d+))?')
    _inet6 = re.compile(r'^\s+inet6 (?P<local>[0-9a-f:]*::[0-9a-f:]+)(?:%\w+)?'
                        r' prefixlen (?P<prefixlen>\d+)'
                        r'(?: (?P<secured>secured))?'
                        r'(?: scopeid (?P<scopeid>0x[0-9a-f]+))?')
    _state = re.compile(r'^\s+status: (?P<state>\w+)')
    _vlan = re.compile(r'^\s+vlan: (?P<vlanid>\d+) parent interface: (?P<parent><?\w+>?)')
    _bond = re.compile(r'^\s+bond interfaces: (\w+(?: \w+)*)')
    _bridge = re.compile(r'^\s+Configuration:')

    def __init__(self, line):
        self.header = self._header.match(line)
        self.eflags = self._eflags.match(line)
        self.ether = self._ether.match(line)
        self.inet = self._inet.match(line)
        self.inet6 = self._inet6.match(line)
        self.state = self._state.match(line)
        self.vlan = self._vlan.match(line)
        self.bond = self._bond.match(line)
        self.bridge = self._bridge.match(line)


class bridgeRegEx:
    _id = re.compile(r'^\s+id (?P<id>(?:[0-9a-fA-F]{1,2}:?){6})'
                     r' priority (?P<priority>\d+)'
                     r' hellotime (?P<hello>\d+)'
                     r' fwddelay (?P<delay>\d+)')
    _age = re.compile(r'^\s+maxage (?P<max_age>\d+)'
                      r' holdcnt (?P<hold>\d+)'
                      r' proto (?P<protocol>\w+)'
                      r' maxaddr (?P<addr>\d+)'
                      r' timeout (?P<ageing>\d+)')
    _root = re.compile(r'^\s+root id (?P<id>(?:[0-9a-fA-F]{1,2}:?){6})'
                       r' priority (?P<priority>\d+)'
                       r' ifcost (?P<cost>\d+)'
                       r' port (?P<port>\d+)')
    _filter = re.compile(r'^\s+ipfilter (?P<filter>\w+)'
                         r' flags (?P<flags>0x[0-9a-fA-F]+)')
    _member = re.compile(r'^\s+member: (?P<member>\w+)')
    _cache = re.compile(r'^\s+media:')

    def __init__(self, line):
        self.id = self._id.match(line)
        self.age = self._age.match(line)
        self.root = self._root.match(line)
        self.filter = self._filter.match(line)
        self.member = self._member.match(line)
        self.cache = self._cache.match(line)


def parse_bridge(lines, links, link):
    info_data = {}
    while line := next(lines):
        match = bridgeRegEx(line)

        if match.id:
            info_data['forward_delay'] = int(match.id.group('delay'))
            info_data['hello_time'] = int(match.id.group('hello'))
        elif match.age:
            info_data['max_age'] = int(match.age.group('max_age'))
            info_data['ageing_time'] = int(match.age.group('ageing'))
        elif match.root:
            info_data['priority'] = int(match.root.group('priority'))
            info_data['root_id'] = match.root.group('id')
            info_data['root_port'] = int(match.root.group('port'))
            info_data['root_path_cost'] = int(match.root.group('cost'))
        elif match.filter:
            info_data['ipfilter'] = match.filter.group('filter') != 'disabled'
        elif match.member:
            slave = next(item for item in links if item['ifname'] == match.member.group('member'))
            slave['master'] = link['ifname']
            slave['linkinfo'] = {'info_slave_kind': 'bridge'}
        elif match.cache:
            link['linkinfo'].update({'info_data': info_data})
            break


def parse(res, option={}):
    links = []
    lines = iter(res.split('\n'))
    while line := next(lines):
        match = ifconfigRegEx(line)

        if match.header:
            header = match.header.groupdict()
            link = {
                'ifindex': int(header['ifindex']),
                'ifname': header['ifname'],
                'flags': header['flags'].split(',') if header['flags'] != '' else [],
                'mtu': int(header['mtu']),
                'operstate': 'UNKNOWN',
                'link_type': 'none'
            }

            if 'LOOPBACK' in link['flags']:
                link['link_type'] = 'loopback'
                link['address'] = '00:00:00:00:00:00'
                link['broadcast'] = '00:00:00:00:00:00'
            elif 'POINTOPOINT' in link['flags']:
                link['link_pointtopoint'] = True

            if (link['ifname'].startswith('bridge')
                or link['ifname'].startswith('bond')
                or link['ifname'].startswith('vlan')):
                link['linkinfo'] = {'info_kind': re.sub(r'[0-9]+', '', link['ifname'])}

            links.append(link)
            continue

        if match.eflags:
            link['eflags'] = match.eflags.group('eflags').split(',')
        elif match.ether:
            link['link_type'] = 'ether'
            link['address'] = match.ether.group(1)
            link['broadcast'] = 'ff:ff:ff:ff:ff:ff'
        elif match.state:
            link['operstate'] = oper_states[match.state.group('state')]
        elif match.inet:
            a = match.inet.groupdict()
            addr = {
                'family': 'inet',
                'local': a['local']
            }
            if a['address']:
                addr['address'] = a['address']
            addr['prefixlen'] = netmask_to_length(a['netmask'])
            if a['broadcast']:
                addr['broadcast'] = a['broadcast']
            link['addr_info'] = link.get('addr_info', []) + [addr]
        elif match.inet6:
            a = match.inet6.groupdict()
            addr = {
                'family': 'inet6',
                'local': a['local'],
                'prefixlen': int(a['prefixlen'])
            }
            link['addr_info'] = link.get('addr_info', []) + [addr]
        elif match.vlan:
            parent = match.vlan.group('parent')
            if parent != '<none>':
                link['link'] = parent
            link['linkinfo'].update({
                'info_data': {
                    'protocol': '802.1Q',
                    'id': int(match.vlan.group('vlanid')),
                    'flags': []
                }
            })
        elif match.bond:
            for ifname in match.bond.group(1).split(' '):
                slave = next(item for item in links if item['ifname'] == ifname)
                slave['master'] = link['ifname']
                slave['address'] = link['address']
                slave['linkinfo'] = {
                    'info_slave_kind': 'bond',
                    'perm_hwaddr': slave['address']
                }
        elif match.bridge:
            parse_bridge(lines, links, link)

    return links


def links(argv, option):
    cmd = subprocess.run(['ifconfig', '-v', '-a'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         encoding="utf-8")
    if cmd.returncode != 0:
        print(cmd.stderr)
        exit(cmd.returncode)

    option['preferred_family'] = AF_PACKET
    links = parse(cmd.stdout, option=option)
    while argv:
        opt = argv.pop(0)
        if opt == 'up':
            links = [link for link in links if ('flags' in link and 'UP' in link['flags'])]
        elif opt == 'group':
            try:
                group = argv.pop(0)
            except IndexError:
                missarg('group name')
            do_notimplemented()
            invarg('Invalid "group" value', group)
        elif opt == 'master':
            try:
                master = argv.pop(0)
            except IndexError:
                missarg('master device')
            if not any(link['ifname'] == master for link in links):
                invarg('Device does not exist', master)
            links = [link for link in links if ('master' in link and link['master'] == master)]
        elif opt == 'master':
            try:
                master = argv.pop(0)
            except IndexError:
                missarg('vrf device')
            if not any(link['ifname'] == master for link in links):
                invarg('Not a valid VRF name', master)
            links = [link for link in links if ('master' in link and link['master'] == master)]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            do_notimplemented()
        elif opt == 'type':
            try:
                kind = argv.pop(0)
            except IndexError:
                missarg('link type')
            if kind.endswith('_slave'):
                kind = kind.replace('_slave', '')
                links = [link for link in links if recurse_in(link, ['linkinfo', 'info_slave_kind'], kind)]
            else:
                links = [link for link in links if recurse_in(link, ['linkinfo', 'info_kind'], kind)]
        elif 'help'.startswith(opt):
            do_iplink_usage()
        else:
            if opt == 'dev':
                try:
                    opt = argv.pop(0)
                except IndexError:
                    error('Command line is not complete. Try option "help"')
            links = [link for link in links if link['ifname'] == opt]
            if not links:
                stderr('Device "%s" does not exist.' % opt)
                exit(-1)

    if not option['show_details']:
        delete_keys(links, ['linkinfo'])

    return links
