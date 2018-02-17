#!/usr/bin/env python
"""Converts iptables syslog entries to vis.js datas."""

import sys
import re
import socket

# IPTABLES wih SRC un DST
# iptRE=re.compile("(\w+\s+\d+\s+\d+:\d+:\d+).+SRC=([\d.]+)\s+DST=([\d.]+)\s.*TTL=([\d]+)\s+ID=([\d]+)\s+.*PROTO=(TCP|UDP)\s+SPT=(\d+)\s+DPT=(\d+).*")
# IPTABLES wih SRC un DST
# iptRE_noSRC=re.compile("(\w+\s+\d+\s+\d+:\d+:\d+).+SRC=([\d.]+)\s+DST=([\d.]+)\s.*TTL=([\d]+)\s+ID=([\d]+)\s+.*PROTO=(\d+)")


# ============================================================================
#   CONSTANTS
# ============================================================================

SRC = 3
DST = 4

# ============================================================================
#   FUNCTIONS
# ============================================================================


def get_name_value(line):
    """Return hash from line containing k=v couples separated by space.

    v must not contains space.
    example:

        line="k1=v1 k2=v2 k3=v3"
        returns {'k1': 'v1', 'k2': 'v2', 'k3': 'v3' }
    """
    values = {}

    for i in line.split():
        try:
            (k, v) = i.split('=')
            values[k] = v
        except:
            values[i] = ''

    return values


def get_host_name(ip):
    """Get host by addr with error catch up."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return 'unknown'


def get_color_from_ip(ip):
    """Get color depending on ip values.

    Returns rgb(a,b,c)  for ipv4 a.b.c.d.
    Returns #XXXXXX for ipv6 with XXXXXX the last 6 values from ip.
    """
    try:
        return "rgb(%s,%s,%s)" % tuple(ip.split('.')[:3])
    except:
        return "#%s" % ip.replace(':', '')[-6:].upper()


def viz_from_iptables_log(data, mode=''):
    """Create 2 hash from iptables logs passed to the function with data parameter.

    - nodes contains all nodes informations
    - vis_edges contains all relations between 2 nodes

    To view 'proto/port' as node, set mode to 'proto_as_node'

    Actually data are red from s
    """
    cur_id = 1
    nodes = {}
    vis_edges = {}

    for l in data:
        v = get_name_value(l[l.find('IN='):].strip())

        try:
            src = v['SRC']
            dst = v['DST']
            proto = v['PROTO'].lower()

            if proto in ('udp', 'tcp'):
                if v['SPT'] == '53':
                    port = v['SPT']
                else:
                    port = v['DPT']
            else:
                port = 'proto'

        except:
            sys.stderr.write("Error - %s\n" % v)
            continue

        if src not in nodes:
            nodes[src] = (cur_id, 'src', get_host_name(src))
            cur_id += 1
        if dst not in nodes:
            nodes[dst] = (cur_id, 'dst', get_host_name(dst))
            cur_id += 1

        proto_label = "%s/%s" % (proto, port)
        if mode != 'proto_as_node':
            edge = "%s_%s_%s_%s" % (src, proto, port, dst)
            if edge in vis_edges:
                vis_edges[edge]['value'] += 1
            else:
                vis_edges[edge] = {}
                vis_edges[edge]['value'] = 1
                vis_edges[edge]['from'] = nodes[src][0]
                vis_edges[edge]['to'] = nodes[dst][0]
                vis_edges[edge]['title'] = proto_label

        else:
            if proto_label not in nodes:
                nodes[proto_label] = (cur_id, 'port', 'port')
                cur_id += 1

            # print "%s ---(%s/%s) ---> %s" % (src, proto,port,dst)
            tagin = "%s_%s" % (src, proto_label)
            tagout = "%s_%s" % (proto_label, dst)

            if tagin in vis_edges:
                vis_edges[tagin]['value'] += 1
            else:
                vis_edges[tagin] = {}
                vis_edges[tagin]['value'] = 1
                vis_edges[tagin]['from'] = nodes[src][0]
                vis_edges[tagin]['to'] = nodes[proto_label][0]
                vis_edges[tagin]['title'] = ''

            if tagout in vis_edges:
                vis_edges[tagout]['value'] += 1
            else:
                vis_edges[tagout] = {}
                vis_edges[tagout]['value'] = 1
                vis_edges[tagout]['from'] = nodes[proto_label][0]
                vis_edges[tagout]['to'] = nodes[dst][0]
                vis_edges[tagout]['title'] = ''

    return (nodes, vis_edges)


if __name__ == '__main__':

    # mode='proto_as_node'
    mode = ''

    packets = sys.stdin.readlines()

    (nodes, vis_edges) = viz_from_iptables_log(packets, mode)

    print("var nodes = new vis.DataSet([")
    for k in nodes.keys():
        if nodes[k][1] == 'src':
            # shape="shape: 'box', color:'#7BE141'"
            shape = "shape: 'box', color:'%s'" % get_color_from_ip(k)

        elif nodes[k][1] == 'dst':
            # shape="shape: 'circle', color:'#FB7E81'"
            shape = "shape: 'circle', color:'%s'" % get_color_from_ip(k)

        elif nodes[k][1] == 'port':
            shape = "shape: 'circle', color:'#FFFF00'"

        print("    {id: %s, label: '%s\\n%s', %s}," %
              (nodes[k][0], nodes[k][2], k, shape))
    print(']);')

    print("var edges = new vis.DataSet([")

    for k in sorted(vis_edges):
        print("{from: %s, to: %s, value: %s, label: '%s', arrows:'to', title:'%s'}," %
              (vis_edges[k]['from'], vis_edges[k]['to'], vis_edges[k]['value'],
               vis_edges[k]['title'], vis_edges[k]['value']))

    print(']);')


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
