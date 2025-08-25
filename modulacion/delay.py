import copy
from operator import attrgetter 
import time 
from ryu.topology.switches import LLDPPacket
from ryu.topology.switches import Switches
from conexion import Neo4jConnection
from ryu.base import app_manager
from ryu.base.app_manager import lookup_service_brick
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,DEAD_DISPATCHER
from ryu.lib import hub

from ryu.ofproto import ofproto_v1_3
from ryu.topology.api import get_all_link
import insert_database


class delay(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    """
        A Ryu app for calculating link delay by using echo replay
        messages from the Control Plane to the datapaths in the Data Plane.
        It is part of the Statistics module s   of the Control Plane
        
    """

    def __init__(self, *args, **kwargs):
       
        super(delay, self).__init__(*args, **kwargs)

        self.topology=app_manager.lookup_service_brick('insert_Database')
        self.sending_echo_request_interval = 0.3
        self.sw_module = lookup_service_brick('switches')
        self.datapaths = {}
        self.echo_latency = {}
        self.link_delay = {}
        self.lldp_delay={}
        self.delay_dict = {}
        self.links_delay={}
        self.measure_thread = hub.spawn(self._detector)

    

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
            Explore LLDP packet and get the delay of link (fwd and reply).
        """
        msg = ev.msg
       
        try:
            time1=time.time()
                
            src_dpid, src_port_no = LLDPPacket.lldp_parse(msg.data)
            dpid =  msg.datapath.id 
             
            if self.sw_module is None:
                self.sw_module = lookup_service_brick('switches')

            for port in self.sw_module.ports.keys():
                if src_dpid == port.dpid and src_port_no == port.port_no:
                    timestamp= self.sw_module.ports[port].timestamp
                    delay =(time1-timestamp)
        
                    #print("El delay es ",delay)
                    self._save_lldp_delay(src=src_dpid, dst=dpid,
                                            lldpdelay=delay)
        except LLDPPacket.LLDPUnknownFormat as e:
            return
    
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('Register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('Unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]
    

    def _detector(self):
        """
            Delay detecting functon.
            Send echo request and calculate link delay periodically
        """

        while True:
    
            if self.topology is not None:
                self.logger.info("🚀 insert_Dtabase detectado")
                
                self.send_echo_request()
                self.create_link_delay()
                self.save_latency()
                hub.sleep(8)
            else:
                self.topology=lookup_service_brick('insert_Database')
            
    
    def send_echo_request(self):
        for datapath in self.datapaths.values():
            now=time.time()
            data1="%.12f" % now 
            data1=data1.encode()
            parser = datapath.ofproto_parser
            echo_req = parser.OFPEchoRequest(datapath,
                                             data=data1 )
            datapath.send_msg(echo_req)
            hub.sleep(self.sending_echo_request_interval)

    @set_ev_cls(ofp_event.EventOFPEchoReply, MAIN_DISPATCHER)
    def echo_reply_handler(self, ev):
        """ Maneja los EchoReply para calcular delay switch ↔ controlador """
        
        now_timestamp = time.time()
        try:
            data=eval(ev.msg.data)
            
            
            latency = now_timestamp - data
            dpid = ev.msg.datapath.id
            self.echo_latency[dpid] = latency
            #print("delay de controlador",latency)
            
        except:
            print("NO FUNCIONO")
            pass
       
    def _save_lldp_delay(self, src=0, dst=0, lldpdelay=0):
        try:
            key=(src,dst)
            
            self.lldp_delay[key]=lldpdelay
            #print("SALVADO")
            
        except:
            print(" NO SALVADO")
            return   


    def create_link_delay(self):
        """
            Create link delay data, and save it into graph object.
        """
        for key in self.topology.links.items():
            
            key=str(key).split(",")
            src=int(key[0].replace('(',''))
            dst=int(key[1].replace(')',''))
            delay = self.get_delay(src, dst)
            
            provicionalkey=(src,dst)
            

            self.links_delay[provicionalkey]= delay

        self.get_link_delay()
    def get_link_delay(self):
        '''
        Calculates total link dealy and save it in self.link_delay[(node1,node2)]: link_delay
        '''       
        for key in self.links_delay.items():
            
            key=str(key).split(",")
            src=int(key[0].replace('(',''))
            dst=int(key[1].replace(')',''))
            key=(src,dst)
            ikey=(dst,src)
            delay1 = self.links_delay[key]
            delay2 = self.links_delay[ikey]
            link_delay = ((delay1 + delay2)*1000.0)/2 #saves in ms
            self.link_delay[key]=link_delay
  

    def get_delay(self, src, dst):
        src=int(src)
        dst=int(dst)
        key=(src,dst)
        ikey=(dst,src)
        try:
           
            src_latency = self.echo_latency[src]
            dst_latency = self.echo_latency[dst]
            
            fwd_delay = self.lldp_delay[key]
            re_delay = self.lldp_delay[ikey]
            
            delay = (fwd_delay + re_delay - src_latency - dst_latency)/2
           
           
            return max(delay, 0)
        except:
            return float('inf')
        

    def save_latency(self):
        all_links=get_all_link(self)       
        for link in copy.copy(all_links):
            
            key=(link.src.dpid,link.dst.dpid)
            delay=self.link_delay[key]
            print("El delay es ",delay,"En el link",key)
            driver=Neo4jConnection.start_connection()

            quarry=f""" 
                   MATCH (a:Switch {{switch_dpid:{link.src.dpid}}})
                   -[r:Link]->
                   (b:Switch{{switch_dpid:{link.dst.dpid}}}) 
                   SET r.delay='{delay}'
                   
            """
            Neo4jConnection.excute_querry(driver,quarry)
                
            Neo4jConnection.close_connection(driver)



