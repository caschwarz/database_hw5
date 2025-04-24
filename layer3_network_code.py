"""
This is a network simulator that simulates 3 routes with 2 hosts connected to each of them
"""

# imports
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class CustomTopo(Topo):
    def build(self):
        # Create routers
        routerA = self.addNode('rA', cls=LinuxRouter, ip='20.10.100.1/24')
        routerB = self.addNode('rB', cls=LinuxRouter, ip='20.10.100.2/24')
        routerC = self.addNode('rC', cls=LinuxRouter, ip='20.10.100.3/24')

        # Hosts for LAN A (/26)
        hA1 = self.addHost('hA1', ip='20.10.172.129/26', defaultRoute='via 20.10.172.129')
        hA2 = self.addHost('hA2', ip='20.10.172.130/26', defaultRoute='via 20.10.172.129')
        self.addLink(hA1, routerA, intfName2='rA-eth1', params2={'ip': '20.10.172.129/26'})
        self.addLink(hA2, routerA, intfName2='rA-eth2')

        # Hosts for LAN B (/25)
        hB1 = self.addHost('hB1', ip='20.10.172.1/25', defaultRoute='via 20.10.172.1')
        hB2 = self.addHost('hB2', ip='20.10.172.2/25', defaultRoute='via 20.10.172.1')
        self.addLink(hB1, routerB, intfName2='rB-eth1', params2={'ip': '20.10.172.1/25'})
        self.addLink(hB2, routerB, intfName2='rB-eth2')

        # Hosts for LAN C (/27)
        hC1 = self.addHost('hC1', ip='20.10.172.193/27', defaultRoute='via 20.10.172.193')
        hC2 = self.addHost('hC2', ip='20.10.172.194/27', defaultRoute='via 20.10.172.193')
        self.addLink(hC1, routerC, intfName2='rC-eth1', params2={'ip': '20.10.172.193/27'})
        self.addLink(hC2, routerC, intfName2='rC-eth2')

        # Inter-router links (shared /24)
        self.addLink(routerA, routerB, intfName1='rA-eth3', intfName2='rB-eth3',
                     params1={'ip': '20.10.100.1/24'}, params2={'ip': '20.10.100.2/24'})
        self.addLink(routerB, routerC, intfName1='rB-eth4', intfName2='rC-eth3',
                     params1={'ip': '20.10.100.4/24'}, params2={'ip': '20.10.100.3/24'})

"""
This function runs the main part of the program. It begins by creating host and routers and defining the links
between them. Then, it displays data on the connectivity info.
"""
def run():
    topo = CustomTopo()
    net = Mininet(topo=topo, switch=OVSKernelSwitch, controller=None, link=TCLink, autoSetMacs=True)
    net.start()

    hA1, hA2 = net.get('hA1'), net.get('hA2')
    hB1, hB2 = net.get('hB1'), net.get('hB2')
    hC1, hC2 = net.get('hC1'), net.get('hC2')
    rA, rB, rC = net.get('rA'), net.get('rB'), net.get('rC')

    # Add static routes on hosts
    for h in [hA1, hA2]:
        h.cmd('route add -net 20.10.172.0 netmask 255.255.255.128 gw 20.10.172.129')
        h.cmd('route add -net 20.10.172.192 netmask 255.255.255.224 gw 20.10.172.129')

    for h in [hB1, hB2]:
        h.cmd('route add -net 20.10.172.128 netmask 255.255.255.192 gw 20.10.172.1')
        h.cmd('route add -net 20.10.172.192 netmask 255.255.255.224 gw 20.10.172.1')

    for h in [hC1, hC2]:
        h.cmd('route add -net 20.10.172.0 netmask 255.255.255.128 gw 20.10.172.193')
        h.cmd('route add -net 20.10.172.128 netmask 255.255.255.192 gw 20.10.172.193')

    # Add static routes on routers
    rA.cmd('route add -net 20.10.172.0 netmask 255.255.255.128 gw 20.10.100.2')
    rA.cmd('route add -net 20.10.172.192 netmask 255.255.255.224 gw 20.10.100.2')

    rB.cmd('route add -net 20.10.172.128 netmask 255.255.255.192 gw 20.10.100.1')
    rB.cmd('route add -net 20.10.172.192 netmask 255.255.255.224 gw 20.10.100.3')

    rC.cmd('route add -net 20.10.172.128 netmask 255.255.255.192 gw 20.10.100.2')
    rC.cmd('route add -net 20.10.172.0 netmask 255.255.255.128 gw 20.10.100.2')

    print("\n===== Testing Intra-LAN Connectivity =====")
    net.ping([hA1, hA2])
    net.ping([hB1, hB2])
    net.ping([hC1, hC2])

    print("\n===== Testing Inter-LAN Connectivity =====")
    net.pingAll()

    print("\n===== Traceroute from hA1 to hC1 =====")
    print(hA1.cmd('traceroute 20.10.172.193'))

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()