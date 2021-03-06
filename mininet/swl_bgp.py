#!/usr/bin/python

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##############################################################################
# Topology with two switches and two hosts with BGP
#
#       2ffe:0101::/64          2ffe:0010::/64         2ffe:0102::/64
#       172.16.101.0/24         172.16.10.0/24         172.16.102.0./24
#  h1 ------------------- sw1 ------------------ sw2------- -------------h2
#     .5               .1     .1               .2   .1                  .5
##############################################################################

from mininet.net import Mininet, VERSION
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from distutils.version import StrictVersion
from p4_mininet import P4DockerSwitch
from time import sleep
import sys

def main(cli=0, ipv6=0):
    net = Mininet( controller = None )

    # add hosts
    h1 = net.addHost( 'h1', ip = '172.16.101.5/24', mac = '00:04:00:00:00:02' )
    h2 = net.addHost( 'h2', ip = '172.16.102.5/24', mac = '00:05:00:00:00:02' )

    # add switch 1
    sw1 = net.addSwitch( 'sw1', target_name = "p4dockerswitch",
            cls = P4DockerSwitch, config_fs = 'configs/sw1/l3_bgp',
            pcap_dump = True )

    # add switch 2
    sw2 = net.addSwitch( 'sw2', target_name = "p4dockerswitch",
            cls = P4DockerSwitch, config_fs = 'configs/sw2/l3_bgp',
            pcap_dump = True )

    # add links
    if StrictVersion(VERSION) <= StrictVersion('2.2.0') :
        net.addLink( sw1, h1, port1 = 1 )
        net.addLink( sw1, sw2, port1 = 2, port2 = 2 )
        net.addLink( sw2, h2, port1 = 1 )
    else:
        net.addLink( sw1, h1, port1 = 1, fast=False )
        net.addLink( sw1, sw2, port1 = 2, port2 = 2, fast=False )
        net.addLink( sw2, h2, port1 = 1, fast=False )

    net.start()

    # hosts configuration - ipv4
    h1.setDefaultRoute( 'via 172.16.101.1' )
    h2.setDefaultRoute( 'via 172.16.102.1' )

    if ipv6:
        # hosts configuration - ipv6
        h1.setIP6('2ffe:0101::5', 64, 'h1-eth0')
        h2.setIP6('2ffe:0102::5', 64, 'h2-eth0')
        h1.setDefaultRoute( 'via 2ffe:0101::1', True )
        h2.setDefaultRoute( 'via 2ffe:0102::1', True )

    sw1.cmd( 'service quagga start')
    sw2.cmd( 'service quagga start')

    result = 0
    if cli:
        CLI( net )
    else:
        sleep(30)

        node_values = net.values()
        print node_values

        hosts = net.hosts
        print hosts

        # ping hosts
        print "PING BETWEEN THE HOSTS"
        result = net.ping(hosts,30)

        if result != 0:
            print "PING FAILED BETWEEN HOSTS %s"  % (hosts)
        else:
            print "PING SUCCESSFUL!!!"

        if ipv6:
            # ping6 hosts
            print "PING6 BETWEEN THE HOSTS"
            result = net.ping6(hosts, 30)
            if result != 0:
                print "PING6 FAILED BETWEEN HOSTS %s" % (hosts)
            else:
                print "PING6 SUCCESSFUL!!!"

        # print host arp table & routes
        for host in hosts:
            print "ARP ENTRIES ON HOST"
            print host.cmd('arp -n')
            print "HOST ROUTES"
            print host.cmd('route')
            print "HOST INTERFACE LIST"
            intfList = host.intfNames()
            print intfList


    net.stop()
    return result

if __name__ == '__main__':
    args = sys.argv
    setLogLevel( 'info' )
    cli = 0
    ipv6 = 0
    if "--cli" in args:
        cli = 1

    if "--ipv6" in args:
        ipv6 = 1

    main(cli, ipv6)
