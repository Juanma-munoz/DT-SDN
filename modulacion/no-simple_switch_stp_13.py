import copy
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.app import simple_switch_13
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology import event
from ryu.topology.api import get_switch,get_link,get_host,get_all_link
from conexion import Neo4jConnection
from ryu.topology import event


class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.switch_created=[]
        self.stp = kwargs['stplib']

        # Sample of stplib config.
        #  please refer to stplib.Stp.set_config() for details.
        config = {dpid_lib.str_to_dpid('0000000000000001'):
                  {'bridge': {'priority': 0x8000}},
                  dpid_lib.str_to_dpid('0000000000000002'):
                  {'bridge': {'priority': 0x9000}},
                  dpid_lib.str_to_dpid('0000000000000003'):
                  {'bridge': {'priority': 0xa000}}}
        self.stp.set_config(config)

    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match)
            datapath.send_msg(mod)

    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    def _topology_change_handler(self, ev):
        dp = ev.dp
        dpid_str = dpid_lib.dpid_to_str(dp.id)
        msg = 'Receive topology change event. Flush MAC table.'
        #self.logger.debug("[dpid=%s] %s", dpid_str, msg)

        if dp.id in self.mac_to_port:
            self.delete_flow(dp)
            del self.mac_to_port[dp.id]

    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    def _port_state_change_handler(self, ev):
        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                    stplib.PORT_STATE_BLOCK: 'BLOCK',
                    stplib.PORT_STATE_LISTEN: 'LISTEN',
                    stplib.PORT_STATE_LEARN: 'LEARN',
                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
        #self.logger.debug("[dpid=%s][port=%d] state=%s",
        #                  dpid_str, ev.port_no, of_state[ev.port_state]) 
    
    @set_ev_cls(event.EventSwitchEnter,MAIN_DISPATCHER)
    def get_swtichs(self):
        #"""Manejador del evento cuando un switch es detectado."""
        switch_list = get_switch(self) 
        print("La lista es:",switch_list)
        for sw in switch_list:
                if(sw.dp.id not in self.switch_created):
                    print("LALALALALA",sw,"\n")
                    driver=Neo4jConnection.start_connection()
                # print("se crea el switch con dpid",sw.dp.id)
                    query = f"""
                        MERGE (Switch:Switch {{switch_dpid:{sw.dp.id}}})
                        """
                    Neo4jConnection.excute_querry(driver,query)
                    Neo4jConnection.close_connection(driver) 
                    self.switch_created.append(sw.dp.id)  
    # @set_ev_cls(stplib.EventTopologyChange)
    # def get_agreatelink(self,ev):
    #     all_links=get_link(self)
    #     self.link=all_links
        
    #     for link in copy.copy(all_links):
    #         key=(link.src.dpid,link.dst.dpid)
              

        
    #         if key not in self.links:
    #             driver=Neo4jConnection.start_connection()
                        
    #             quarry=f""" 
    #                             MATCH (s:Switch {{switch_dpid: {link.src.dpid}}})
    #                             MATCH (d:Switch {{switch_dpid: {link.dst.dpid}}})
    #                             MERGE (s)-[l:Link {{Origen:  'S{link.src.dpid}', Destino: 'S{link.dst.dpid}'}}]->(d)
    #                             SET l.OrigenPuerto={link.src.port_no},l.DestinoPuerto={link.dst.port_no}
    #                             """
    #             Neo4jConnection.excute_querry(driver,quarry)
    #             Neo4jConnection.close_connection(driver)