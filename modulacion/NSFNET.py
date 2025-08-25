from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Node
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections

class NFSNETTopo( Topo ):
    "Internet Topology Zoo Specimen."

    def addSwitch( self, name, **opts ):
            kwargs = { 'protocols' : 'OpenFlow13' }
            kwargs.update( opts )
            return super(NFSNETTopo, self).addSwitch( name, **kwargs )
    
    def __init__( self ):
        "Create a topology."

        # Initialize Topology
        Topo.__init__( self )

        ########################CREACION DE LOS SWITCHES########################
        seattle = self.addSwitch('s1')
        palo_Alto = self.addSwitch('s2') 
        san_Diego = self.addSwitch('s3')
        salt_Lake_City = self.addSwitch('s4')
        boukler= self.addSwitch('s5')
        lincon= self.addSwitch('s6')
        champaign= self.addSwitch('s7') 
        pittburgh= self.addSwitch('s8')
        princeton = self.addSwitch('s9')
        cottege_Park = self.addSwitch('s10') 
        ithaca = self.addSwitch('s11')  
        ann_Arbor = self.addSwitch('s12')
        atlanta = self.addSwitch('s13')
        houston = self.addSwitch('s14')

        ########################CREACION DE LOS HOSTS########################

        seattle_HOST = self.addHost('h1')
        palo_Alto_HOST = self.addHost('h2') 
        san_Diego_HOST = self.addHost('h3')
        salt_Lake_City_HOST = self.addHost('h4')
        boukler_HOST= self.addHost('h5')
        lincon_HOST= self.addHost('h6')
        champaign_HOST= self.addHost('h7') 
        pittburgh_HOST= self.addHost('h8')
        princeton_HOST = self.addHost('h9')
        cottege_Park_HOST = self.addHost('h10') 
        ithaca_HOST = self.addHost('h11')  
        ann_Arbor_HOST = self.addHost('h12')
        atlanta_HOST = self.addHost('h13')
        houston_HOST = self.addHost('h14')

        ########################CREACION DE LOS LINKS ENTRE SWITCH Y HOSTS########################


        self.addLink( seattle , seattle_HOST )
        self.addLink( palo_Alto , palo_Alto_HOST )
        self.addLink( san_Diego  , san_Diego_HOST  )
        self.addLink( salt_Lake_City_HOST , salt_Lake_City )
        self.addLink( boukler , boukler_HOST )
        self.addLink( lincon , lincon_HOST )
        self.addLink( champaign , champaign_HOST )
        self.addLink( pittburgh , pittburgh_HOST )
        self.addLink( princeton , princeton_HOST )
        self.addLink( cottege_Park , cottege_Park_HOST )
        self.addLink( ithaca , ithaca_HOST )
        self.addLink( ann_Arbor , ann_Arbor_HOST )
        self.addLink( atlanta , atlanta_HOST )
        self.addLink( houston , houston_HOST )

        #################CREACION DE LINKS ENTRE SWITCH######################
        self.addLink(seattle,palo_Alto)
        self.addLink(seattle,san_Diego)
        self.addLink(seattle,champaign)
        self.addLink(palo_Alto,salt_Lake_City)
        self.addLink(palo_Alto,san_Diego)
        self.addLink(san_Diego,houston)
        self.addLink(salt_Lake_City,boukler)
        self.addLink(salt_Lake_City,ann_Arbor)
        self.addLink(boukler,lincon)
        self.addLink(boukler,houston)
        self.addLink(lincon,champaign)
        self.addLink(champaign,pittburgh)
        self.addLink(pittburgh,ithaca)
        self.addLink(pittburgh,princeton)
        self.addLink(pittburgh,atlanta)
        self.addLink(atlanta,houston)
        self.addLink(houston,cottege_Park)
        self.addLink(cottege_Park,ithaca)
        self.addLink(cottege_Park,princeton)
        self.addLink(princeton,ann_Arbor)
        self.addLink(ann_Arbor,ithaca)


topos = { 'NSFNET': ( lambda: NFSNETTopo() ) }
if __name__ == '__main__':
    setLogLevel('info')
    topo = NFSNETTopo()
    net = Mininet(topo=topo, controller=RemoteController)
    net.start()
    CLI(net)
    net.stop()