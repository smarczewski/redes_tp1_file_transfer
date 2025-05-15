from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.term import makeTerm
import time


class MyTopo(Topo):
    def build(self):
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        h4 = self.addHost("h4")

        s1 = self.addSwitch("s1")

        self.addLink(h1, s1, cls=TCLink, loss=10)
        self.addLink(h2, s1, cls=TCLink, loss=0)
        self.addLink(h3, s1, cls=TCLink, loss=0)
        self.addLink(h4, s1, cls=TCLink, loss=0)


topo = MyTopo()
net = Mininet(topo=topo, link=TCLink)
net.start()

h1 = net.get("h1")
h2 = net.get("h2")
h3 = net.get("h3")
h4 = net.get("h4")


makeTerm(h1, title="Host h1 - Servidor",
         cmd="python3 start-server.py -v -H10.0.0.1 -p12000 -s./server_files -r")

time.sleep(1)

makeTerm(h2, title="Host h2 - Cliente Subida",
         cmd="python3 upload.py -v -H10.0.0.1 -p12000 -s./client_files -nfile_3.jpg -r;read")
makeTerm(h3, title="Host h3 - Cliente Descarga",
         cmd="python3 download.py -v -H10.0.0.1 -p12000 -d./client_files -nfile_1.jpg -r;read")
makeTerm(h4, title="Host h4 - Cliente Descarga",
         cmd="python3 download.py -v -H10.0.0.1 -p12000 -d./client_files -nfile_2.jpg -r;read")

CLI(net)

net.stop()
