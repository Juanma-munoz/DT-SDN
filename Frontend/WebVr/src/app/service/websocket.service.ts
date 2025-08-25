import { Injectable } from '@angular/core';
import { Socket,io } from 'socket.io-client';
@Injectable({
  providedIn: 'root'
})
export class WebsocketService {

  private websocket:Socket;

  constructor() { 
    this.websocket=io('http://localhost:5000')
  }
  public getSocket(){
    return this.websocket
  }


  public listenToServerMessages(): any {
    let packets:any=[];
    this.websocket.on('icmp_packet', (data) => {
        packets.push(data)
        console.log(data)
      return packets
    });
  }

  public sendMessage(message: any,asunto:string): void {
    this.websocket.emit(asunto, message);
  }
}
