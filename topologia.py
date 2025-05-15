from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.term import makeTerm


class MyTopo(Topo):
    def build(self):
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")

        s1 = self.addSwitch("s1")

        self.addLink(h1, s1, cls=TCLink, loss=5)
        self.addLink(h2, s1, cls=TCLink, loss=5)


topo = MyTopo()
net = Mininet(topo=topo, link=TCLink)
net.start()

h1 = net.get("h1")
h2 = net.get("h2")

makeTerm(h1, title="Host h1")
makeTerm(h2, title="Host h2")

CLI(net)

net.stop()
