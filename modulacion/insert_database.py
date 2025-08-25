import copy
from conexion import Neo4jConnection
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER,CONFIG_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event
from ryu.topology.api import get_switch,get_link,get_host,get_all_link
from ports import Port
import networkx as nx
import matplotlib.pyplot as plt
from ryu.lib import hub
from ryu.lib import stplib


class insert_Database(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    """
        A ryu app to discover a topology and insert in NEO4J data base 
    """


    def __init__(self, *args, **kwargs):
        super(insert_Database, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.name = 'insert_Database'
        driver=Neo4jConnection.start_connection()
        Neo4jConnection.clearNeo4j(driver)
        Neo4jConnection.close_connection(driver)
        self.switch_ports = {}
        self.switch_created=[]
        self.host_created=[]
        self.link_to_port={}   
        self.links={}
        self.port_features={}
        self.monitor=hub.spawn(self.fidelity)

        self.neo4j_graph=nx.Graph()
        self.mininet_graph=nx.Graph()
        self.link={}
        self.host={}
        self.switch={}
        
        
    
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        
        datapath = ev.msg.datapath
        
        self.request_port_desc(datapath)

    def request_port_desc(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortDescStatsRequest(datapath)
        datapath.send_msg(req)
        
    #@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    #def _packet_in_handler(self, ev):
    #     self.save_host(self)
    
    @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    def get_port(self, ev):
        """Manejador del evento que recibe la descripción de los puertos."""
        msg = ev.msg
        datapath = ev.msg.datapath
        dpid = datapath.id  # Identificador del switch
        ports = ev.msg.body
        ofproto = msg.datapath.ofproto
        self.port_features.setdefault(dpid, {})
        config_dict = {ofproto.OFPPC_PORT_DOWN: "Down",
                        ofproto.OFPPC_NO_RECV: "No Recv",
                        ofproto.OFPPC_NO_FWD: "No Farward",
                        ofproto.OFPPC_NO_PACKET_IN: "No Packet-in"}

        state_dict = {ofproto.OFPPS_LINK_DOWN: "Down",
                       ofproto.OFPPS_BLOCKED: "Blocked",
                       ofproto.OFPPS_LIVE: "Live"}
        ports = []
        for p in ev.msg.body:
            if p.port_no != 1:

                ports.append('port_no=%d hw_addr=%s name=%s config=0x%08x '
                             'state=0x%08x curr=0x%08x advertised=0x%08x '
                             'supported=0x%08x peer=0x%08x curr_speed=%d '
                             'max_speed=%d' %
                             (p.port_no, p.hw_addr,
                              p.name, p.config,
                              p.state, p.curr, p.advertised,
                              p.supported, p.peer, p.curr_speed,
                              p.max_speed))
                if p.config in config_dict:
                    config = config_dict[p.config]
                else:
                    config = "up"

                if p.state in state_dict:
                    state = state_dict[p.state]
                else:
                    state = "up"

                # Recording data.
                port_feature = [config, state,p.curr_speed]

                self.port_features[dpid][p.port_no] = port_feature   
                
        list_switch_port = []
        for p in ev.msg.body:
            
            port_no = p.port_no
            port_state = "DOWN" if p.state == datapath.ofproto.OFPPS_LINK_DOWN else "UP"
            port_name = p.name.decode('utf-8')
            
            switch_port = Port(port_no, port_state, port_name)
            #print(f"Switch {dpid} - Puerto {port_no}: {port_state} ({port_name})")
            list_switch_port.append(switch_port)
        
        # Almacena los puertos en el diccionario
        self.switch_ports[dpid] = list_switch_port

    @set_ev_cls(event.EventSwitchEnter,MAIN_DISPATCHER)
    def get_swtichs(self,ev):
        #"""Manejador del evento cuando un switch es detectado."""
        switch_list = get_switch(self) 
        self.switch=switch_list
        for sw in switch_list:
          
            if(sw.dp.id not in self.switch_created):
                driver=Neo4jConnection.start_connection()
                query = f"""
                    MERGE (Switch:Switch {{switch_dpid:{sw.dp.id}}})
                    """
                Neo4jConnection.excute_querry(driver,query)
                
               
                contador=0
                ports = self.switch_ports.get(sw.dp.id, [])

                
                if(ports):
                    for port in ports:
                        
                      #  print("El switch DPID",sw.dp.id,"el numero",port.id,"el dpid",port.number)
                        query1 = f"""
                                MATCH (s:Switch {{switch_dpid: {sw.dp.id}}})
                                SET s.puerto{contador}_numero = {port.id},
                                    s.puerto{contador}_dpid = "{port.number}",
                                    s.port{contador}_status = "{port.status}"
                                RETURN s
                                """
                        Neo4jConnection.excute_querry(driver,query1)
                        contador=contador+1
                self.switch_created.append(sw.dp.id)           
                Neo4jConnection.close_connection(driver) 
                
        
            
               
                
    # @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    # def get_agreatelink(self,ev):
    #     all_links=get_link(self)
    #     self.link=all_links
        
    #     for link in copy.copy(all_links):
    #         key=(link.src.dpid,link.dst.dpid)
        
    #         if key not in self.links:
    #             driver=Neo4jConnection.start_connection()
    #             print("##########################################")
    #             quarry=f""" 
    #                             MATCH (s:Switch {{switch_dpid: {link.src.dpid}}})
    #                             MATCH (d:Switch {{switch_dpid: {link.dst.dpid}}})
    #                             MERGE (s)-[l:Link {{Origen:  'S{link.src.dpid}', Destino: 'S{link.dst.dpid}'}}]->(d)
    #                             SET l.OrigenPuerto={link.src.port_no},l.DestinoPuerto={link.dst.port_no}
    #                             """
    #             Neo4jConnection.excute_querry(driver,quarry)
    #             Neo4jConnection.close_connection(driver)
    #             src = link.src
    #             dst = link.dst
    #             self.link_to_port[(src.dpid, dst.dpid)] = (src.port_no, dst.port_no)
    #             self.links[key]=0
    
      
        
        
    def save_host(self,ev):
        
        hosts=get_host(self,None)
        self.host=hosts
        for host in hosts:
            print("\n",host,"\n")
            if(host.ipv4):
               
                if (host.ipv4 not in  self.host_created):
                    ipv4_address=host.ipv4[0]
                    hostDPID = ipv4_address.split('.')[-1]
                    
                    driver=Neo4jConnection.start_connection()
                    
                    mac=f"'{host.mac}'"
                        
                    quarry=f"""
                        MATCH (s:Switch {{switch_dpid: {host.port.dpid}}})
                        Merge(host:Host{{MAC:{mac},IPv4:{host.ipv4},HostDPID:{hostDPID}}})  
                        MERGE (host)-[l:Link {{Origen: 'H{hostDPID}', Destino: 'S{host.port.dpid}'}}]->(s)
                        """
                    Neo4jConnection.excute_querry(driver,quarry)
                    Neo4jConnection.close_connection(driver)
                    self.host_created.append(host.ipv4)
                    
    def fidelity(self):
        while True:
            self.create_neo4j_graph()
            self.create_mininet_graph()
            self.evaluate_graph()
            hub.sleep(10)
            
    
    def clear_graph(self):
        self.neo4j_graph.clear()
   
    def create_neo4j_graph(self):
       
        driver=Neo4jConnection.start_connection()

        querry_switches="MATCH (s:Switch) RETURN s" 
        querry_links="MATCH p=()-[r:Link]->() RETURN p" 
        querry_host="MATCH (h:Host) RETURN h" 

        switches=Neo4jConnection.topology(driver,querry_switches)
        links=Neo4jConnection.topology(driver,querry_links)
        hosts=Neo4jConnection.topology(driver,querry_host)

        for switch in switches:
            switch_data=switch["s"]
            switch_dpid="S"+str(switch_data['switch_dpid'])
            self.neo4j_graph.add_node(switch_dpid,**switch_data,type="switch")

        for host in hosts:
            host_data=host["h"] 
            host_dpid="H"+str(host_data['HostDPID'])
            self.neo4j_graph.add_node(host_dpid,**host_data,type="host")


        for link in links:
            link_data=link["p"] 
            src_temporal=str(link_data).split('Link')[0]
            dst_temporal=str(link_data).split('Link')[1]
            #print(src_temporal,dst_temporal)

            if(src_temporal.find("IPv4")!= -1 or dst_temporal.find("IPv4")!= -1 ):
                src="H"+src_temporal.split('HostDPID')[1].split(",")[0].replace(":","").replace("'","").strip()
                dst="S"+dst_temporal.split('switch_dpid')[1].split(",")[0].replace(":","").replace("'","").strip()
                self.neo4j_graph.add_edge(src,dst,type="link")

            else:
                src="S"+src_temporal.split('switch_dpid')[1].split(",")[0].replace(":","").replace("'","").strip()
                dst="S"+dst_temporal.split('switch_dpid')[1].split(",")[0].replace(":","").replace("'","").strip()
                self.neo4j_graph.add_edge(src,dst,type="link")
        # Dibujar el grafo
        # plt.figure(figsize=(8, 6))
        # nx.draw(self.neo4j_graph, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=10)
        # plt.show()

    def create_mininet_graph(self):
    
        for sw in self.switch:
            id="S"+str(sw.dp.id)
            self.mininet_graph.add_node(id,type="switch")
        
        for link in self.link:
            src="S"+str(link.src.dpid)
            dst="S"+str(link.dst.dpid)
            self.mininet_graph.add_edge(src,dst,type="link")
        
        for host in self.host:
            id=str(host.ipv4).replace("['","").replace("']","")
            self.mininet_graph.add_node(id,type="host")
        
        for host in self.host:
            src=str(host.ipv4).replace("['","").replace("']","")
            dst="S"+str(host.port.dpid)
            self.mininet_graph.add_edge(src,dst,type="link")

        #Dibujar el grafo
            # plt.figure(figsize=(8, 6))
            # nx.draw(self.neo4j_graph, with_labels=True, node_color="lightblue", edge_color="gray", node_size=2000, font_size=10)
            # plt.show()
        

    def evaluate_graph(self):
        if (self.neo4j_graph and self.mininet_graph):
            ged = nx.graph_edit_distance(self.neo4j_graph, self.mininet_graph)
            #print(f"Diferencia entre Mininet y Neo4j (GED): {ged}")
            is_isomorphic = nx.is_isomorphic(self.neo4j_graph, self.mininet_graph)
            #print(f"¿Los grafos son isomorfos? {is_isomorphic}")
            are_equal = nx.utils.graphs_equal(self.neo4j_graph, self.mininet_graph)
           # print(f"¿Los grafos son idénticos? {are_equal}")