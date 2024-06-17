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
    for l in data:
        dev = l['ifname'] + '@' + l['link'] if 'link' in l else l['ifname']
        desc = 'mtu {}'.format(l['mtu'])
        if 'master' in l:
            desc = '{} master {}'.format(desc, l['master'])
        desc = '{} state {}'.format(desc, l['operstate'])
        lines.append('%d: %s: <%s> %s' % (
            l['ifindex'], dev, ','.join(l['flags']), desc
        ))
        lines.append(
            '    link/' + l['link_type'] +
            ((' ' + l['address']) if 'address' in l else '') +
            ((' brd ' + l['broadcast']) if 'broadcast' in l else '')
        )
        if 'linkinfo' in l and 'info_kind' in l['linkinfo']:
            i = l['linkinfo']
            if i['info_kind'] == 'vlan':
                lines.append(
                    '    %s protocol %s id %d' %
                    (i['info_kind'], i['info_data']['protocol'], i['info_data']['id'])
                )
            elif i['info_kind'] == 'bridge':
                lines.append(
                    '    bridge ' + ' '.join(['%s %s' % (k, v) for k, v in i['info_data'].items()])
                )
        for a in l.get('addr_info', []):
            address = '%s peer %s' % (a['local'], a['address']) if 'address' in a else a['local']
            lines.append(
                '    %s %s/%d' % (a['family'], address, a['prefixlen']) +
                ((' brd ' + a['broadcast']) if 'broadcast' in a else '')
            )
    return '\n'.join(lines)


def dumps(data, option):
    if option['json']:
        print(json_dumps(data, option['pretty']))
    elif data:
        print(text_dumps(data))

def parse(res, option={}):
    links = []
    count = 1

    lines = iter(res.split('\n'))
    while r := next(lines):
        if re.match(r'^\w+:', r):
            if count > 1:
                if 'addr_info' not in link:
                    link['addr_info'] = []
                links.append(link)
            (ifname, flags, mtu, ifindex) = re.findall(r'^(\w+): flags=\d+<(.*)> mtu (\d+) index (\d+)', r)[0]
            flags = flags.split(',') if flags != '' else []
            link = {
                'ifindex': int(ifindex),
                'ifname': ifname,
                'flags': flags,
                'mtu': int(mtu),
                'operstate': 'UNKNOWN',
                'link_type': 'unknown'
            }
            if 'LOOPBACK' in flags:
                link['link_type'] = 'loopback'
                link['address'] = '00:00:00:00:00:00'
                link['broadcast'] = '00:00:00:00:00:00'
            elif 'POINTOPOINT' in flags:
                link['link_type'] = 'none'
                link['link_pointtopoint'] = True
            count = count + 1
        else:
            if re.match(r'^\s+ether ', r):
                link['link_type'] = 'ether'
                link['address'] = re.findall(r'(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)', r)[0]
                link['broadcast'] = 'ff:ff:ff:ff:ff:ff'
            elif re.match(r'^\s+inet ', r) and option['preferred_family'] != AF_INET6:
                (local, netmask) = re.findall(r'inet (\d+\.\d+\.\d+\.\d+).* netmask (0x[0-9a-f]+)', r)[0]
                addr = { 'family': 'inet', 'local': local }
                if re.match(r'^.*-->', r):
                    addr['address'] = re.findall(r'--> (\d+\.\d+\.\d+\.\d+)', r)[0]
                addr['prefixlen'] = netmask_to_length(netmask)
                if re.match(r'^.*broadcast', r):
                    addr['broadcast'] = re.findall(r'broadcast (\d+\.\d+\.\d+\.\d+)', r)[0]
                link['addr_info'] = link.get('addr_info', []) + [addr]
            elif re.match(r'^\s+inet6 ', r) and option['preferred_family'] != AF_INET:
                (local, prefixlen) = re.findall(r'inet6 ([0-9a-f:]*::[0-9a-f:]+)%*\w* prefixlen (\d+)', r)[0]
                link['addr_info'] = link.get('addr_info', []) + [{
                    'family': 'inet6',
                    'local': local,
                    'prefixlen': int(prefixlen)
                }]
            elif re.match(r'^\s+status: ', r):
                link['operstate'] = oper_states[re.findall(r'status: (\w+)', r)[0]]
            elif re.match(r'^\s+vlan: ', r):
                (vid, vlink) = re.findall(r'vlan: (\d+) parent interface: (<?\w+>?)', r)[0]
                link['link'] = vlink
                link['linkinfo'] = {
                    'info_kind': 'vlan',
                    'info_data': {
                        'protocol': '802.1Q',
                        'id': int(vid),
                        'flags': []
                    }
                }
            elif re.match(r'^\s+Configuration:', r):
                link['linkinfo'] = {
                    'info_kind': 'bridge',
                    'info_data': {}
                }
            elif re.match(r'^\s+id .* priority .* hellotime .* fwddelay .*', r):
                (bridge_id, bridge_priority, hello_time, forward_delay) = re.findall(
                    r'id (\w+:\w+:\w+:\w+:\w+:\w+) priority (\d+) hellotime (\d+) fwddelay (\d+)', r)[0]
                link['linkinfo']['info_data'].update(
                    {
                        'forward_delay': forward_delay,
                        'hello_time': hello_time
                    }
                )
                r = next(lines)

                try:
                    (max_age, hold_count, bridge_protocol, max_addr, ageing_time) = re.findall(
                        r'maxage (\d+) holdcnt (\d+) proto (\w+) maxaddr (\d+) timeout (\d+)', r)[0]
                    link['linkinfo']['info_data'].update(
                        {
                            'max_age': max_age,
                            'ageing_time': ageing_time
                        }
                    )
                    r = next(lines)
                except:
                    pass

                try:
                    (root_id, priority, root_path_cost, root_port) = re.findall(
                        r'root id (\w+:\w+:\w+:\w+:\w+:\w+) priority (\d+) ifcost (\d+) port (\d+)', r)[0]
                    link['linkinfo']['info_data'].update(
                        {
                            'priority': priority,
                            'root_id': root_id,
                            'root_port': root_port,
                            'root_path_cost': root_path_cost
                        }
                    )
                    r = next(lines)
                except:
                    pass

                (ipfilter, flags) = re.findall(
                    r'ipfilter (\w+) flags (0x[0-9a-fA-F]+)', r)[0]
                link['linkinfo']['info_data']['ipfilter'] = ipfilter != 'disabled'

            elif re.match(r'^\s+member: ', r):
                dev = re.findall(r'member: (\w+)', r)[0]
                index = next((i for (i, l) in enumerate(links) if l['ifname'] == dev), None)
                links[index]['master'] = ifname
                if 'linkinfo' not in links[index]:
                    links[index]['linkinfo'] = { 'info_slave_kind': 'bridge' }
                else:
                    links[index]['linkinfo']['info_slave_kind'] = 'bridge'

    if count > 1:
        if 'addr_info' not in link:
            link['addr_info'] = []
        links.append(link)

    return links


def list(argv, option):
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
            links = [l for l in links if ('flags' in l and 'UP' in l['flags'])]
        elif opt == 'group':
            try:
                group = argv.pop(0)
            except IndexError:
                missarg('group name')
            do_notimplemented()
            invarg('Invalid "group" value', group);
        elif opt == 'master':
            try:
                master = argv.pop(0)
            except IndexError:
                missarg('master device')
            if not any(l['ifname'] == master for l in links):
                invarg('Device does not exist', master);
            links = [l for l in links if ('master' in l and l['master'] == master)]
        elif opt == 'master':
            try:
                master = argv.pop(0)
            except IndexError:
                missarg('vrf device')
            if not any(l['ifname'] == master for l in links):
                invarg('Not a valid VRF name', master);
            links = [l for l in links if ('master' in l and l['master'] == master)]
            # FIXME: https://wiki.netunix.net/freebsd/network/vrf/
            do_notimplemented()
        elif opt == 'type':
            try:
                kind = argv.pop(0)
            except IndexError:
                missarg('link type')
            if kind.endswith('_slave'):
                kind = kind.replace('_slave', '')
                links = [l for l in links if recurse_in(l, ['linkinfo', 'info_slave_kind'], kind)]
            else:
                links = [l for l in links if recurse_in(l, ['linkinfo', 'info_kind'], kind)]
        elif 'help'.startswith(opt):
            do_iplink_usage()
        else:
            if opt == 'dev':
                try:
                    dev = argv.pop(0)
                except IndexError:
                    error('Command line is not complete. Try option "help"')
                links = [l for l in links if l['ifname'] == dev]
                if not links:
                    stderr('Device "%s" does not exist.' % dev)
                    exit(-1)

    if not option['show_details']:
        delete_keys(links, ['linkinfo'])

    return links
