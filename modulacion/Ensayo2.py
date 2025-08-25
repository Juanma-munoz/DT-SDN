import copy
from operator import attrgetter
import websocket_server 
import threading
import json
import time 
from ryu.topology.switches import Switches
from ryu.topology.switches import LLDPPacket
from ryu.base.app_manager import lookup_service_brick
from conexion import Neo4jConnection
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls,DEAD_DISPATCHER
from ryu.lib import hub
from ryu.lib.packet import lldp
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types,ipv4,icmp
from ryu.topology import event
from ryu.topology.api import get_switch,get_link,get_host,get_all_link
from switch import Switch
from ports import Port
from conexion import Neo4jConnection

import delay



class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
   
    def __init__(self, *args, **kwargs):
        super(SimpleSwitch, self).__init__(*args, **kwargs)
        self.delay = lookup_service_brick('delay')
        self.topology=app_manager.lookup_service_brick('insert_Database')
        
        self.datapaths={}
        self.mac_to_port = {}
        self.monitor=hub.spawn(self._detector)
        self.port_features = {}
        self.flow_stats = {}
        self.flow_speed = {}
        self.flow_loss = {}
        self.port_loss = {}
        self.link_loss = {}
        self.paths={}
        self.count_monitor = 0
        self.topology_api_app = self
        self.stats = {}
        self.port_stats = {}
        self.link_free_bw = {}
        self.link_used_bw = {}
        self.free_bandwidth = {}

        self.datapaths = {}
        self.port_stats = {}
        self.port_speed = {}
        self.flow_stats = {}
        self.flow_speed = {}
        self.flow_loss = {}
        self.port_loss = {}
        self.link_loss = {}
        self.net_info = {}
        self.net_metrics= {}
        self.link_free_bw = {}
        self.link_used_bw = {}
        self.stats = {}
        self.port_features = self.topology.port_features
        self.free_bandwidth = {}
        self.paths = {}
        self.installed_paths = {}
        self.speed_counter=0


        self.web_server_thread = threading.Thread(target=websocket_server.start_websocket_server)
        self.web_server_thread.setDaemon(True)
        self.web_server_thread.start()


   
    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
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
        hub.sleep(1)

        while True:


            if self.delay is not None:
                
                self.count_monitor += 1
                self.stats['flow'] = {}
                self.stats['port'] = {}
                print("[Statistics Module Ok]")
                print("[{0}]".format(self.count_monitor))
                
                for dp in self.datapaths.values():
                    self.port_features.setdefault(dp.id, {}) #setdefault() returns the value of the item with the specified key
                    self.paths = None
                    self.request_stats(dp)
                hub.sleep(1)
                
                if self.stats['port']:
                    print("ESTY AQUI ")
                    self.get_port_loss()
                    self.get_link_free_bw()
                    self.get_link_used_bw()
                    
                hub.sleep(1)
                if self.stats['port']:
                    #self.show_stat('link') 
                    None
            else:
                print('No monitor')
                self.delay = lookup_service_brick('delay')     
            
    def request_stats(self, datapath): #OK
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        req = parser.OFPPortDescStatsRequest(datapath, 0) #for port description 
        datapath.send_msg(req)

        req = parser.OFPFlowStatsRequest(datapath) #individual flow statistics
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY) 
        datapath.send_msg(req)

    


    def get_link_free_bw(self):
        #Calculates the total free bw of link and save it in self.link_free_bw[(node1,node2)]:link_free_bw
        for dp in self.free_bandwidth.keys():
            for port in self.free_bandwidth[dp]:
                free_bw1 = self.free_bandwidth[dp][port]
                key2 = self.get_sw_dst(dp, port) #key2 = (dp,port)
                free_bw2= self.free_bandwidth[key2[0]][key2[1]]
                free_bw1=free_bw1[0]
                free_bw2=free_bw2[0]

        
                link_free_bw = (free_bw1 + free_bw2)/2
                link = (dp, key2[0])
                self.link_free_bw[link] = link_free_bw
               # print("el ancho de banda libre del link",link_free_bw, "del link",link)
                self.save_free_bw()

        
    def get_link_used_bw(self):
        #Calculates the total free bw of link and save it in self.link_free_bw[(node1,node2)]:link_free_bw
        for key in self.port_speed.keys():
            used_bw1 = self.port_speed[key][-1]
            key2 = self.get_sw_dst(key[0], key[1]) #key2 = (dp,port)
            used_bw2 = self.port_speed[key2][-1]
            link_used_bw = (used_bw1 + used_bw2)/2
            link = (key[0], key2[0])
            self.link_used_bw[link] = link_used_bw
            #print("el ancho de banda usado del link",link_used_bw, "del link",link)
            self.save_throughput()

    def get_sw_dst(self, dpid, out_port):
        for key in self.topology.link_to_port:
            src_port = self.topology.link_to_port[key][0]
            if key[0] == dpid and src_port == out_port:
                dst_sw = key[1]
                dst_port = self.topology.link_to_port[key][1]
                return (dst_sw, dst_port)



    def save_stats(self, _dict, key, value, length=5): 
        if key not in _dict:
            _dict[key] = []
        _dict[key].append(value)
        if len(_dict[key]) > length:
            _dict[key].pop(0)           
    
    
    
    def get_flow_loss(self):
        #Get per flow loss
        bodies = self.stats['flow']
        for dp in bodies.keys():
            list_flows = sorted([flow for flow in bodies[dp] if flow.priority == 1], 
                                key=lambda flow: (flow.match.get('ipv4_src'),flow.match.get('ipv4_dst')))
            for stat in list_flows:
                out_port = stat.instructions[0].actions[0].port
                if self.awareness.link_to_port and out_port != 1: #get loss form ports of network
                    key = (stat.match.get('ipv4_src'), stat.match.get('ipv4_dst'))
                    tmp1 = self.flow_stats[dp][key]
                    byte_count_src = tmp1[-1][1]
                    
                    result = self.get_sw_dst(dp, out_port)
                    dst_sw = result[0]
                    tmp2 = self.flow_stats[dst_sw][key]
                    byte_count_dst = tmp2[-1][1]
                    flow_loss = byte_count_src - byte_count_dst
                    self.save_stats(self.flow_loss[dp], key, flow_loss, 5)


    def get_period(self, n_sec, n_nsec, p_sec, p_nsec): # (time las flow, time)
                                                         # calculates period of time between flows
        return self.get_time(n_sec, n_nsec) - self.get_time(p_sec, p_nsec)
    
    def get_speed(self, now, pre, period): #bits/s
        if period:
            return ((now - pre)*8) / period
        else:
            return 0
    def get_time(self, sec, nsec): #Total time that the flow was alive in seconds
        return sec + nsec / 1000000000.0 
    
   
    def get_port_loss(self):
        #Get loss_port
        bodies = self.stats['port']
        for dp in sorted(bodies.keys()):
            for stat in sorted(bodies[dp], key=attrgetter('port_no')):
                if self.topology.link_to_port and stat.port_no != 1 and stat.port_no != ofproto_v1_3.OFPP_LOCAL: #get loss form ports of network
                    key1 = (dp, stat.port_no)
                    tmp1 = self.port_stats[key1]
                    tx_bytes_src = tmp1[-1][0]
                    tx_pkts_src = tmp1[-1][8]

                    key2 = self.get_sw_dst(dp, stat.port_no)
                    tmp2 = self.port_stats[key2]
                    rx_bytes_dst = tmp2[-1][1]
                    rx_pkts_dst = tmp2[-1][9]
                    loss_port = float(tx_pkts_src - rx_pkts_dst) / tx_pkts_src #loss rate
                    values = (loss_port, key2)
                    self.save_stats(self.port_loss[dp], key1, values, 5)
        #Calculates the total link loss and save it in self.link_loss[(node1,node2)]:loss
        for dp in self.port_loss.keys():
            for port in self.port_loss[dp]:
                key2 = self.port_loss[dp][port][-1][1]
                loss_src = self.port_loss[dp][port][-1][0]
                # tx_src = self.port_loss[dp][port][-1][1]
                loss_dst = self.port_loss[key2[0]][key2][-1][0]
                # tx_dst = self.port_loss[key2[0]][key2][-1][1]
                loss_l = (abs(loss_src) + abs(loss_dst)) / 2
                link = (dp, key2[0])
                self.link_loss[link] = loss_l*100.0 #loss in porcentage
                #print("LAS PERIDAS SON ",loss_l*100.0,"del enlace",link)
                self.save_packet_loss()
                


     
    ##############################METODOS CON DECORADORES############################
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER) #OK
    def flow_stats_reply_handler(self, ev):
        body = ev.msg.body 
        #print(f'Aqui: {body}')
        dpid = ev.msg.datapath.id 
        #print(f'{dpid}')
        self.stats['flow'][dpid] = body 
        #print(f'{self.stats}')
        self.flow_stats.setdefault(dpid, {}) 
        self.flow_speed.setdefault(dpid, {})
        self.flow_loss.setdefault(dpid, {})

        
        for stat in sorted([flow for flow in body if flow.priority == 5 and flow.priority != 65535 ],                           
                           key=lambda flow: (flow.match.get('eth_src'),
                                             flow.match.get('in_port'),
                                             flow.match.get('eth_dst'))):
            key = (stat.match.get('in_port'),stat.match.get('eth_src'), stat.match.get('eth_dst'))
            
            value = (stat.packet_count, stat.byte_count,
                        stat.duration_sec, stat.duration_nsec)
            self.speed_counter += 0
            
            #value = (stat.packet_count, stat.byte_count,
                        #stat.duration_sec, stat.duration_nsec)#duration_sec: Time flow was alive in seconds
                                                            #duration_nsec: Time flow was alive in nanoseconds beyond duration_sec
            self.save_stats(self.flow_stats[dpid], key, value, 5)
            #print(f'El valor: {value}')
            #print('--------------------------------------------')
            

                # CALCULATE FLOW BYTE RATE 
            pre = 0
            period =10
            tmp = self.flow_stats[dpid][key]
            #print(f'Este es el tmp: {tmp}')
            if len(tmp)>1:
                pre = tmp[-2][1] #penultimo flow byte_count
                period = self.get_period(tmp[-1][2], tmp[-1][3], #valores  (sec,nsec) ultimo flow, penultimo flow)
                                            tmp[-2][2], tmp[-2][3])
            speed = self.get_speed(self.flow_stats[dpid][key][-1][1], #ultimo flow byte_count, penultimo byte_count, periodo
                                        pre, period)
            self.save_stats(self.flow_speed[dpid], key, speed, 10) #bits/s
            resultado = self.flow_speed[dpid][key]
            #print(f'Este es el tmp: {tmp}')
           # if len(resultado)== 10:
                #print('-----------------------------------------------------------------------------------')
               # promedio_velocidad = sum(resultado)/ len(resultado)
                #print(f'Velocidad: {resultado} bits/s')
                #print('-----------------------------------------------------------------------------------')
                #print(f'Promedio de Velocidad: {promedio_velocidad} bits/s')
            #print(f'{self.speed_counter} = Paquetes: {value[0]}, Bytes: {value[1]}, Velocidad: {speed}')
        
            
            #print(f'Resultado final #: {speed},llave{key}')
            #print(f"Esta es la llave {self.flow_stats}")
            #print(f'{speed}')
                #print(f'{speed}')
                #print('--------------')
                #print(f'{self.flow_speed}')
                #print('--------------')    
    
           
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        a = time.time()
        body = ev.msg.body
        dpid = ev.msg.datapath.id

        self.stats['port'][dpid] = body
        
        self.port_loss.setdefault(dpid, {})
        self.free_bandwidth.setdefault(dpid, {})
        """
            Save port's stats information into self.port_stats.
            Calculate port speed and Save it.
            self.port_stats = {(dpid, port_no):[(tx_bytes, rx_bytes, rx_errors, duration_sec,  duration_nsec),],}
            self.port_speed = {(dpid, port_no):[speed,],}
            Note: The transmit performance and receive performance are independent of a port.
            Calculate the load of a port only using tx_bytes.
        
        Replay message content:
            (stat.port_no,
             stat.rx_packets, stat.tx_packets,
             stat.rx_bytes, stat.tx_bytes,
             stat.rx_dropped, stat.tx_dropped,
             stat.rx_errors, stat.tx_errors,
             stat.rx_frame_err, stat.rx_over_err,
             stat.rx_crc_err, stat.collisions,
             stat.duration_sec, stat.duration_nsec))
        """
       
        for stat in sorted(body, key=attrgetter('port_no')): #get the value of port_no form body
            port_no = stat.port_no
            key = (dpid, port_no) #src_dpid, src_port
            value = (stat.tx_bytes, stat.rx_bytes, stat.rx_errors,
                     stat.duration_sec, stat.duration_nsec, stat.tx_errors, stat.tx_dropped, stat.rx_dropped, stat.tx_packets, stat.rx_packets)
            
            self.save_stats(self.port_stats, key, value, 5)

            if port_no != ofproto_v1_3.OFPP_LOCAL: #si es dif de puerto local del sw donde se lee port        
                if port_no != 1 and self.topology.link_to_port :
                    # Get port speed and Save it.
                    pre = 0
                    period = 10
                    tmp = self.port_stats[key]
                    if len(tmp) > 1:
                        # Calculate with the tx_bytes and rx_bytes
                        pre = tmp[-2][0] + tmp[-2][1] #penultimo port tx_bytes 
                        period = self.get_period(tmp[-1][3], tmp[-1][4], tmp[-2][3], tmp[-2][4]) #periodo entre el ultimo y penultimo total bytes en el puerto
                    speed = self.get_speed(self.port_stats[key][-1][0] + self.port_stats[key][-1][1], pre, period) #speed in bits/s
                   # print("el throughput del enlace es",speed, "de la llave",key)
                    self.save_stats(self.port_speed, key, speed, 5)
                    self._save_freebandwidth(dpid, port_no, speed)

    # @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
    # def port_desc_stats_reply_handler(self, ev):
    #     """
    #         Save port description info.
    #     """
    #     msg = ev.msg
    #     dpid = msg.datapath.id
    #     ofproto = msg.datapath.ofproto

    #     self.port_features.setdefault(dpid, {}) 

    #     config_dict = {ofproto.OFPPC_PORT_DOWN: "Down",
    #                    ofproto.OFPPC_NO_RECV: "No Recv",
    #                    ofproto.OFPPC_NO_FWD: "No Farward",
    #                    ofproto.OFPPC_NO_PACKET_IN: "No Packet-in"}

    #     state_dict = {ofproto.OFPPS_LINK_DOWN: "Down",
    #                   ofproto.OFPPS_BLOCKED: "Blocked",
    #                   ofproto.OFPPS_LIVE: "Live"}

    #     ports = []
    #     for p in ev.msg.body:
    #         if p.port_no != 1:

    #             ports.append('port_no=%d hw_addr=%s name=%s config=0x%08x '
    #                          'state=0x%08x curr=0x%08x advertised=0x%08x '
    #                          'supported=0x%08x peer=0x%08x curr_speed=%d '
    #                          'max_speed=%d' %
    #                          (p.port_no, p.hw_addr,
    #                           p.name, p.config,
    #                           p.state, p.curr, p.advertised,
    #                           p.supported, p.peer, p.curr_speed,
    #                           p.max_speed))
    #             if p.config in config_dict:
    #                 config = config_dict[p.config]
    #             else:
    #                 config = "up"

    #             if p.state in state_dict:
    #                 state = state_dict[p.state]
    #             else:
    #                 state = "up"

    #             # Recording data.
    #             port_feature = [config, state]
    #             self.port_features[dpid][p.port_no] = port_feature   

    def _save_freebandwidth(self, dpid, port_no, speed):
        # Calculate free bandwidth of port and save it.
        port_state = self.port_features.get(dpid).get(port_no)

        if port_state:
            capacity = port_state[2] / (10**3)  # Kbp/s to MBit/s
            speed = float(speed * 8) / (10**6) # byte/s to Mbit/s
            curr_bw = max(capacity - speed, 0)
            self.free_bandwidth[dpid].setdefault(port_no, None)
            self.free_bandwidth[dpid][port_no] = (curr_bw, speed) # Save as Mbit/s
        else:
            self.logger.warning("Fail in getting port state")           
   

    def save_packet_loss(self):
        for link in self.topology.link_to_port:
            
            src=link[0]
            dst=link[1]
            key=(src,dst)
    
            if key in self.link_loss.keys():
                
                perdidas=self.link_loss[key]
                driver=Neo4jConnection.start_connection()
                
                quarry=f""" 
                   MATCH (a:Switch {{switch_dpid:{src}}})
                   -[r:Link]->
                   (b:Switch{{switch_dpid:{dst}}}) 
                   SET r.perdidas='{perdidas}'
                 
                   
                """
                Neo4jConnection.excute_querry(driver,quarry)
                Neo4jConnection.close_connection(driver)
    
    def save_throughput(self):
        for link in self.topology.link_to_port:
            
            src=link[0]
            dst=link[1]
            key=(src,dst)
    
            if key in self.link_used_bw.keys():
                
                bw=self.link_used_bw[key]
             
                driver=Neo4jConnection.start_connection()
                
                quarry=f""" 
                   MATCH (a:Switch {{switch_dpid:{src}}})
                   -[r:Link]->
                   (b:Switch{{switch_dpid:{dst}}}) 
                   SET r.throughput='{bw}'
                          
                """
                Neo4jConnection.excute_querry(driver,quarry)
                Neo4jConnection.close_connection(driver)

           
            
    def save_free_bw(self):
        for link in self.topology.link_to_port:
                    
            src=link[0]
            dst=link[1]
            key=(src,dst)
            
            if key in self.link_free_bw.keys():
                
                free_bw=self.link_free_bw[key]
                        
                driver=Neo4jConnection.start_connection()
                            
                quarry=f""" 
                MATCH (a:Switch {{switch_dpid:{src}}})
                -[r:Link]->
                (b:Switch{{switch_dpid:{dst}}}) 
                SET r.free_bw='{free_bw}'                    
                 """
                
                Neo4jConnection.excute_querry(driver,quarry)
                Neo4jConnection.close_connection(driver)
