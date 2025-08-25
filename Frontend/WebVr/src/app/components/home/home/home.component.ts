import { Component, OnInit } from '@angular/core';
import { GetTopologiaService } from 'src/app/service/get-topologia.service';
import { Port } from 'src/app/interfaces/port';
import { Switches } from 'src/app/interfaces/switches';
import { Host } from 'src/app/interfaces/host.js';
import { Links } from 'src/app/interfaces/links.js';
import { Socket, io } from 'socket.io-client';
import { ICMP } from 'src/app/interfaces/icmp.js';
import { Router } from '@angular/router';
import { linkcounts } from 'src/app/interfaces/linksCount';
import 'src/app/aframe/switch-component.js'
import { Coordenadas } from 'src/app/interfaces/coordenadas';




@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.sass']
})
export class HomeComponent implements OnInit {
  socket: any;
  delayNetwork: number = 0;
  title = 'DigitalTwin';
  listHost: Array<Host> = []
  listSwitch: Array<Switches> = [];
  listPort: Array<Port> = [];
  listLinks: Array<Links> = [];
  packets: Array<ICMP> = [];
  listCoordenadasSwitch: Array<Coordenadas> = [];
  listCoordenadas: Array<Coordenadas> = [];
  coordenadasHost: Array<Coordenadas> = [];
  private websocket: Socket;

  constructor(private Topologia: GetTopologiaService, private router: Router) {
    this.websocket = io('http://localhost:5000', {
      reconnection: true, // Reconexión automática
      reconnectionAttempts: 5,
      reconnectionDelay: 2000
    })

  }

  ngOnInit(): void {


    this.cargarTopologia();
    /*this.websocket.on('icmp_packet',(data:any)=>{
      this.packets=this.procesarICMPMensaje(data)

      console.log(this.packets)
      this.renderPackets(this.packets)
    });
    */
  }


  private cargarTopologia(): void {
    this.Topologia.getSwitches().subscribe((datos: any) => {
      this.listSwitch = this.procesarSwitch(datos);
      //this.renderswitch(this.listSwitch);
    });
    this.Topologia.getHosts().subscribe((datos: any) => {
      this.listHost = this.procesarHosts(datos);

    });

    this.Topologia.getLinks().subscribe((datos: any) => {
      this.listLinks = this.procesarLinks(datos);
      this.renderTopologia(this.listSwitch, this.listLinks)
    });







  }
  private calcularNumeroEnlacesSwitch(Switches: Array<Switches>, Links: Array<Links>): { switchId: string, linksFilter: Array<linkcounts> } {
    let linksFilter: Array<linkcounts> = [];

    let switchId: string = "";
    let comparador = 0;
    for (let t = 0; t < Switches.length; t++) {
      let enlacesTotales: number = 0;
      let enlacesSwitch: number = 0;
      let id: string = 'S' + Switches[t].switch_dpid


      for (let g = 0; g < Links.length; g++) {

        if (Links[g].destino == id || Links[g].origen == id) {
          enlacesTotales = enlacesTotales + 1;
          if (Links[g].destino.startsWith('S') && Links[g].origen.startsWith('S')) {

            enlacesSwitch = enlacesSwitch + 1
          }

        }

      }
      linksFilter.push({
        dpid: id,
        totallinks: enlacesTotales,
        linksSwitch: enlacesSwitch / 2
      });
    }
    for (let r = 0; r < linksFilter.length; r++) {

      if (linksFilter[r].linksSwitch > comparador) {
        comparador = linksFilter[r].linksSwitch;
        switchId = linksFilter[r].dpid

      }
    }

    return { switchId, linksFilter }
  }

  private renderTopologia(Switches: Array<Switches>, Links: Array<Links>): void {
    let coordenas: Array<any> = [];
    const plane = document.getElementById("network")!;
    let LinksCount = this.calcularNumeroEnlacesSwitch(Switches, Links)
    for (let o = 0; o < Switches.length; o++) {
      const Aswitch = document.createElement('a-entity');
      Aswitch.setAttribute('id', `S${Switches[o].switch_dpid.toString()}`);
      Aswitch.setAttribute('geometry', "primitive: box; depth: 1; height: 0.75; width: 2;");
      Aswitch.setAttribute('color', 'blue');


      Aswitch.setAttribute("data", JSON.stringify(this.listSwitch[o]));

      Aswitch.addEventListener("click", (event) => this.showInfoSwitch(event, this.listLinks, this.listSwitch));
      Aswitch.addEventListener("dobleclick", () => this.destroy());
      Aswitch.addEventListener("collide", () => {
        console.log("VIDA SETENTA")
      });

      let boolen: boolean = false
      if (`S${Switches[o].switch_dpid.toString()}` == LinksCount.switchId) {
        boolen = true;
      }

      switch (boolen) {

        case (true):

          Aswitch.setAttribute('position', '0 -2 1');
          let ID: string = `S${Switches[o].switch_dpid.toString()}`
          coordenas.push({
            dpid: ID,
            X: 0,
            Y: -2,
            Z: 1,
          })
          break;

        default:

          if (LinksCount.linksFilter[o].linksSwitch > 2) {
            let total: number = Switches.length
            let radius: number = 7;
            const angle = (2 * Math.PI / total) * o; // Ángulo para este elemento
            const x = Math.round(radius * Math.cos(angle)); // Coordenada X
            const y = Math.round(radius * Math.sin(angle)); // Coordenada Yds
            const z = Math.floor(Math.random() * (2 - (-2) + 1)) + (-2);

            Aswitch.setAttribute('position', `${x} ${y} ${z}`)
            let ID = `S${Switches[o].switch_dpid.toString()}`
            coordenas.push({
              dpid: ID,
              X: x,
              Y: y,
              Z: z,
            })


          } else {
            let total: number = Math.floor(Math.random() * ((Switches.length + 3) - (Switches.length) + 1)) + (Switches.length);
            let radius: number = 8;
            const angle = (2 * Math.PI / total) * o; // Ángulo para este elemento
            const x = Math.round(radius * Math.cos(angle)); // Coordenada X
            const y = Math.round(radius * Math.sin(angle)); // Coordenada Yds
            const z = Math.floor(Math.random() * (2 - (-2) + 1)) + (-2);
            Aswitch.setAttribute('position', `${x} ${y} ${z}`)
            let ID = `S${Switches[o].switch_dpid.toString()}`
            coordenas.push({
              dpid: ID,
              X: x,
              Y: y,
              Z: z,
            })
          }
      }
      //Aswitch.setAttribute('position', this.calcularPosicionCircular(o, Switches.length, radius));
      plane.appendChild(Aswitch);
    }
    for (let j = 0; j < Switches.length; j++) {
      const provicionalSwitch = document.getElementById(`S${Switches[j].switch_dpid.toString()}`);
      const text = document.createElement("a-text");
      text.setAttribute('value', `S${Switches[j].switch_dpid.toString()}`);
      text.setAttribute('color', `white`);
      text.setAttribute('align', `center`);
      text.setAttribute('width', `10`);
      text.setAttribute('position', '0 0 0.51');
      provicionalSwitch?.appendChild(text);

    }
    this.renderHosts1(this.listHost, this.listLinks, coordenas)

    let coordenadasController: any = this.renderControlador()
    this.renderEnlacesSwitch(this.listLinks, coordenas)
    this.renderEnlacesControlador(this.listLinks, coordenadasController, coordenas)
  }

  private procesarSwitch(datos: any): Array<Switches> {
    return datos.map((item: any) => {
      const switches = item.switches;

      const switch_dpid = switches.switch_dpid.low;
      const ports: Port[] = [];

      // Iteramos sobre las claves de switches para construir los puertos
      for (const key in switches) {
        if (key.startsWith('puerto') && key.includes('_dpid')) {
          const portIndex = key.match(/\d+/)?.[0]; // Extraemos el número del puerto
          if (portIndex !== undefined) {
            const dpid = switches[key];
            const statusKey = `port${portIndex}_status`;
            const numberKey = `puerto${portIndex}_numero`;

            const status = switches[statusKey] === 'Up';
            const number = switches[numberKey]?.low ?? 0;

            ports.push({ dpid, status, number });
          }
        }
      }

      return { switch_dpid, Port: ports };
    });
  }

  private procesarHosts(datos: any): Array<Host> {
    return datos.map((item: any) => {
      const hosts = item.hosts;

      const HostDPID: string = 'H' + hosts.HostDPID.low;
      const MAC = hosts.MAC
      const IP = JSON.stringify(hosts.IPv4)

      return { HostDPID, MAC, IP };
    });
  }

  private renderHosts1(Hosts: Array<Host>, Links: Array<Links>, CoordenadaSwtich: Array<any>): void {

    let coordenadasHosts: Array<any> = []

    const plane = document.getElementById("network")!;

    Hosts.forEach((host) => {


      // Obtener el switch correspondiente al host
      let switchid = Links.find(link => link.destino == host.HostDPID)?.origen;

      // Obtener las coordenadas del switch
      let coordenada = CoordenadaSwtich.find(coord => coord.dpid == switchid);
      if (!coordenada) {
        console.error(`Coordenadas no encontradas para el switch ${switchid}`);
        return;
      }

      let { X, Y } = coordenada;
      let cuadrate = 0;
      let angle = 0;

      // Determinar el cuadrante y calcular el ángulo
      if (X >= 0 && Y >= 0) {
        cuadrate = 1;
        angle = Math.random() * (Math.PI / 2); // Primer cuadrante

      } else if (X < 0 && Y > 0) {
        cuadrate = 2;
        angle = (Math.PI / 2) + Math.random() * (Math.PI / 2); // Segundo cuadrante

      } else if (X <= 0 && Y <= 0) {
        cuadrate = 3;
        angle = Math.PI + Math.random() * (Math.PI / 2); // Tercer cuadrante

      } else if (X > 0 && Y < 0) {
        cuadrate = 4;
        angle = (3 * Math.PI / 2) + Math.random() * (Math.PI / 2); // Cuarto cuadrante

      }

      // Crear entidad gráfica para el host
      const Ahost = document.createElement('a-obj-model');
      Ahost.setAttribute('src', '#computer-obj');
      Ahost.setAttribute('material', 'src:assets/computer.jpg');
      Ahost.setAttribute('rotation', '-90 0 0');
      Ahost.setAttribute('scale', '0.05 0.05 0.05');
      Ahost.setAttribute('id', `${host.HostDPID}`);
      Ahost.setAttribute('IPv4', `${host.IP}`);
      //Ahost.setAttribute('gotohosts', '');

      // Calcular la posición final del host
      const Xpos = Math.round(X + 4 * Math.cos(angle));
      const Ypos = Math.round(Y + 4 * Math.sin(angle));
      const Zpos = Math.floor(Math.random() * 5) - 2; // Generar Z entre -2 y 2

      Ahost.setAttribute('position', `${Xpos} ${Ypos} ${Zpos}`);
      Ahost.setAttribute('static-body', '');
    
      plane.appendChild(Ahost);


      coordenadasHosts.push({
        dpid: host.HostDPID,
        X: Xpos,
        Y: Ypos,
        Z: Zpos,
      })




    });
    for (let j = 0; j < Hosts.length; j++) {

      const provicionalHost = document.getElementById(`${Hosts[j].HostDPID}`);
      const text = document.createElement("a-text");
      text.setAttribute('value', `${Hosts[j].HostDPID}`);
      text.setAttribute('color', `white`);
      text.setAttribute('aling', `center`);
      text.setAttribute('scale', `25 25 25`);
      text.setAttribute('position', '-2.5a -1 32');
      text.setAttribute('rotation', '90 0 0');
      provicionalHost?.appendChild(text);
    }
    this.coordenadasHost = coordenadasHosts;
    this.rednerEnlacesHosts(Links, CoordenadaSwtich, coordenadasHosts)
  }

  private procesarLinks(datos: any): Array<Links> {
    let delay = 0;
    let throughput = 0;
    let id = 1;
    return datos.map((item: any) => {

      if (item[0].relationship.delay == null) {
        delay = NaN
      } else {
        delay = item[0].relationship.delay
      }
      if (item[0].relationship.throughput == null) {
        delay = NaN
      } else {
        throughput = item[0].relationship.throughput
      }




      const origen = item[0].relationship.Destino
      const destino = item[0].relationship.Origen
      const loss = item[0].relationship.perdidas
      const origenPuerto = item[0].relationship.DestinoPuerto
      const destinoPuerto = item[0].relationship.OrigenPuerto
      const linkId = id
      id = id + 1;

      return { linkId, origen, destino, origenPuerto, destinoPuerto, delay, loss, throughput };

    });
  }
  private rednerEnlacesHosts(Links: Array<Links>, CoordenasSwitch: Array<any>, CoordenadasHosts: Array<any>): void {
    console.log(this.listLinks)

    const plane = document.getElementById("network")!;


    Links.forEach(link => {


      // Buscar las coordenadas del origen y destino
      const origen = CoordenasSwitch.find(CoordenadasSwitch => CoordenadasSwitch.dpid == link.origen)
      const destino = CoordenadasHosts.find(CoordenadaHost => CoordenadaHost.dpid === link.destino);


      if (origen && destino) {


        // Extraer coordenadas
        const srcX = origen.X, srcY = origen.Y, srcZ = origen.Z;
        const dstX = destino.X, dstY = destino.Y, dstZ = destino.Z;



        // Crear la línea
        const linea = document.createElement('a-entity');
        linea.setAttribute(
          'line',
          `start: ${srcX} ${srcY} ${srcZ}; end: ${dstX} ${dstY} ${dstZ}; color: black;`
        );
        linea.setAttribute('id', `${link.origen}-${link.destino}`);
        plane.appendChild(linea);

        //console.log(  `Línea creada exitosamente: Origen (${srcX},${srcY},${srcZ}) -> Destino (${dstX},${dstY},${dstZ})`);
      }
      else {
        //console.warn(
        //  `No hosts se encontró una de las coordenadas para el enlace: origen = ${link.origen}, destino = ${link.destino}`
        //);
      }

    });





  }

  private renderEnlacesSwitch(Links: Array<Links>, Coordenas: Array<any>): void {
    let angleX: number, angleY: number;
    let angleZ: number = 0;
    const plane = document.getElementById("network")!;


    Links.forEach(link => {
      // Buscar las coordenadas del origen y destino
      const origen = Coordenas.find(coordenada => coordenada.dpid === link.origen);
      const destino = Coordenas.find(coordenada => coordenada.dpid === link.destino);

      if (origen && destino) {
        // Extraer coordenadas
        const srcX = origen.X, srcY = origen.Y, srcZ = origen.Z;
        const dstX = destino.X, dstY = destino.Y, dstZ = destino.Z;

        // Calcular la posición central del cilindro
        const centerX = (srcX + dstX) / 2;
        const centerY = (srcY + dstY) / 2;
        const centerZ = (srcZ + dstZ) / 2;

        // Calcular la distancia entre los puntos (para la altura del cilindro)
        const dx = dstX - srcX;
        const dy = dstY - srcY;
        const dz = dstZ - srcZ;
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);



        if (dy == 0 && dx == 0) {
          angleZ = Math.atan2(dx, dz) * (180 / Math.PI);

        } else {

          // Calcular la rotación del cilindro usando ángulos de Euler
          angleX = Math.atan2(Math.sqrt(dx * dx + dz * dz), dy) * (180 / Math.PI);
          angleY = Math.atan2(dx, dz) * (180 / Math.PI);
        }

        const exite = document.getElementById(`${link.origen}-${link.destino}`)
        const exite1 = document.getElementById(`${link.destino}-${link.origen}`)

        if (!exite1 && !exite) {





          // Crear el cilindro
          const cilindro = document.createElement('a-entity');
          cilindro.setAttribute('geometry', `primitive: cylinder; radius: 0.15; height: ${distance};`);
          cilindro.setAttribute('material', 'color: black;');
          cilindro.setAttribute('position', `${centerX} ${centerY} ${centerZ}`);
          cilindro.setAttribute('rotation', `${angleX} ${angleY} ${angleZ}`);
          cilindro.setAttribute('id', `${link.origen}-${link.destino}`);
          cilindro.addEventListener("click", (event) => this.showInfoLink(event));
          // Agregar eventos de hover


          // Agregar al escenario
          plane.appendChild(cilindro);
        }
      } else {
        //console.warn(`No se encontró una de las coordenadas para el enlace: origen = ${link.origen}, destino = ${link.destino}`);
      }
    });
  }





  private renderControlador(): any {
    const controllerX = 0;
    const controllerY = 3;
    const controllerZ = 4


    const plane = document.getElementById("network")!;
    const controller = document.createElement("a-box")
    controller.setAttribute("position", '0 3 4')
    controller.setAttribute("id", 'controlador')
    controller.setAttribute("height", "1")
    controller.setAttribute("width", "2")
    plane.append(controller)



    const controlador = document.getElementById("controlador")
    const text = document.createElement("a-text")
    text.setAttribute('value', 'controller');
    text.setAttribute('color', `black`);
    text.setAttribute('aling', `center`);
    text.setAttribute('width', `10`);
    text.setAttribute('position', '-0.9 0 0.51');
    controlador?.appendChild(text)


    let coordenas = {
      X: controllerX, Y: controllerY, Z: controllerZ
    }

    return coordenas

  }

  private renderEnlacesControlador(links: Array<Links>, CoordenadaController: any, coordenadasSwtch: Array<any>): void {
    const plane = document.getElementById("network")!;

    links.forEach(link => {
      const Coord = coordenadasSwtch.find(coordenada => coordenada.dpid == link.origen)
      const X = Coord.X
      const Y = Coord.Y
      const Z = Coord.Z

      const existe = document.getElementById(`${link.origen}-Controlador `)
      if (!existe) {



        const linea = document.createElement('a-entity');
        linea.setAttribute(
          'line',
          `start: ${X} ${Y} ${Z}; end: ${CoordenadaController.X} ${CoordenadaController.Y} ${CoordenadaController.Z}; color: black;`
        );
        linea.setAttribute('id', `${link.origen}-Controlador `);
        plane.appendChild(linea);
      }

    })
  }

  private getDelayNetwork(RTT: number): void {
    if (RTT != 0) {
      let delay: number
      this.delayNetwork = RTT
      delay = (RTT / 2) * 1000
      const Adelay = document.getElementById('delay')
      Adelay?.setAttribute('value', `${delay.toFixed(3)}ms`)
    }
  }


  private showInfoSwitch(event: any, listLinks: Array<Links>, listSwitch: Array<Switches>): void {
    //Declaracion de variables
    const distance: number = 3
    //Obtencion de elementos por ID
    const network = document.getElementById("network")
    const camara = document.getElementById("camara")
    const sky = document.getElementById("entorno")

    //Creacion de nuevos elementos
    const entorno = document.createElement('a-sky')

    //Destruccion del entorno
    sky?.remove()

    //Seteo de nuevos atributos
    entorno.setAttribute("id", "entorno")
    entorno?.setAttribute("src", 'assets/fondoLinks1.jpg')
    camara?.setAttribute("position", "350 0 350")
    camara?.setAttribute("rotation", "0 0 0")
    //camara?.setAttribute("position","5 0 0")


    //Agregar nuevo entorno
    network?.appendChild(entorno)


    //Obtencion de la poscion y rotacion de la camara
    const rotationS = camara?.getAttribute("rotation")
    const cameraRot = JSON.parse(JSON.stringify(rotationS))
    const cameraPos = JSON.parse(JSON.stringify(camara?.getAttribute("position")))
    const x = cameraPos.x + distance * Math.sin(cameraRot.y * (Math.PI / 180));
    const z = cameraPos.z - distance * Math.cos(cameraRot.y * (Math.PI / 180));

    //Creacion y seteo de los  del TV para visualizar los datos
    const board = document.createElement('a-obj-model');
    board.setAttribute('src', '#TV-obj');
    board.setAttribute('id', 'board');
    board.setAttribute('material', 'src:assets/TV.jpg');
    board.setAttribute('scale', '0.05 0.05 0.05');
    board.setAttribute("position", `${x} ${cameraPos.y - 1} ${z}`)
    board.setAttribute("rotation", "-90 0 0")
    network?.appendChild(board)


     //Creacion de la puerta de salida
     const puerta = document.createElement('a-obj-model');
     puerta.setAttribute('src', '#puerta-obj');
     puerta.setAttribute('material', 'src:assets/puerta.jpg');
     puerta.setAttribute('id', 'puerta')
     puerta.setAttribute('scale', '0.02 0.02 0.02');
     puerta.setAttribute("position", `${x} ${cameraPos.y + 1} ${z + 5}`)
     puerta.setAttribute("rotation", "90 0 0")
     puerta.addEventListener('click', () => { this.destroy() })
     network?.appendChild(puerta)

     //Obtencion del id del link al cual se esta mirando
     const switchId = event.target.getAttribute("id")
 
     /*Creacion,seteo del texto con el valor del switch al cual se esta mirando 
       y agregar al TV de visulizacion */
     const text = document.createElement("a-text");
     text.setAttribute("value", `Switch ${switchId}`);
     text.setAttribute("id", `Switch ${switchId}`);
     text.setAttribute("position", `0 -2,850 63`);
     text.setAttribute("align", "center");
     text.setAttribute("color", "white");
     text.setAttribute("scale", "30 30 1");
     text.setAttribute("rotation", "90 0 0");
     board?.appendChild(text)


    //Creacion,seteo y agregacion del texto con el titulo de las perdidas al TV de visulizacion
    const portNumber = document.createElement('a-text')
    portNumber.setAttribute("value", 'Port Number')
    portNumber.setAttribute("id", 'portNumber');
    portNumber.setAttribute("align", "center");
    portNumber.setAttribute("color", "red");
    portNumber.setAttribute("scale", "15 15 1");
    portNumber.setAttribute("rotation", "90 0 0");
    portNumber.setAttribute("position", `-27 -2,850 56`);
    board?.appendChild(portNumber)
    let contador:number=1
    let textPorts:Array<any>=[]
    listSwitch.forEach((swtich)=>{
      if(swtich.switch_dpid==switchId.replace('S','')){
        
        swtich.Port.forEach((port)=>{
          let textPort=document.createElement("a-text")
          textPort.setAttribute('value', `${port.number}`)
          textPort.setAttribute("position", `-27 -2,850 ${56-(contador*5)}`)
          textPort.setAttribute("id", `portnumber${port.number}`);
          textPort.setAttribute("align", "center")
          textPort.setAttribute("rotation", "90 0 0");
          textPort.setAttribute("color", "white");
          textPort.setAttribute("scale", "15 15 1");
          board?.appendChild(textPort)
          contador=contador+1

          if(port.number==-2)
          {
            textPort.setAttribute('value', `4294967294`)
            textPorts.push(port.number)
            return
          }
          textPorts.push(port.number)
        })

      }
    })
    
     //Creacion,seteo y agregacion del texto con el titulo de las perdidas al TV de visulizacion
     const textDestination = document.createElement('a-text')
     textDestination.setAttribute("value", 'Destination')
     textDestination.setAttribute("id", 'textDestination');
     textDestination.setAttribute("align", "center");
     textDestination.setAttribute("color", "red");
     textDestination.setAttribute("scale", "15 15 1");
     textDestination.setAttribute("rotation", "90 0 0");
     textDestination.setAttribute("position", `0 -2,850 56`);
     board?.appendChild(textDestination)

    listSwitch.forEach((sw)=>{
      if(sw.switch_dpid==switchId.replace('S','')){
        sw.Port.forEach((port)=>{
        let portnumber=String(port.number)
        let valuePort=document.createElement("a-text")
        let switchDestino=listLinks.find(link=> link.origen==switchId && link.origenPuerto==portnumber)
       
        //Para el caso del puerto que conecta al controlador
        if(portnumber=="-2"){
          valuePort.setAttribute('value', `Controlador`)
          valuePort.setAttribute("position", `0 -2,850 ${56-((textPorts.indexOf(parseInt(portnumber))+1)*5)}`)
          valuePort.setAttribute("id", `portnumber:4294967294`);
          valuePort.setAttribute("align", "center")
          valuePort.setAttribute("rotation", "90 0 0");
          valuePort.setAttribute("color", "white");
          valuePort.setAttribute("scale", "15 15 1");
          board?.appendChild(valuePort)
         }
       
         
         
         //Para el caso de que el puerto vaya a los hosts del switch
         if(!switchDestino && portnumber!="-2"){
          valuePort.setAttribute('value', `Host`)
          valuePort.setAttribute("position", `0 -2,850 ${56-((textPorts.indexOf(parseInt(portnumber))+1)*5)}`)
          valuePort.setAttribute("id", `portnumber${port.number}`);
          valuePort.setAttribute("align", "center")
          valuePort.setAttribute("rotation", "90 0 0");
          valuePort.setAttribute("color", "white");
          valuePort.setAttribute("scale", "15 15 1");
          board?.appendChild(valuePort)
          }
         if(switchDestino){
          console.log(switchDestino.destinoPuerto)
          valuePort.setAttribute('value', `${switchDestino?.destino}-${switchDestino.destinoPuerto}`)
          valuePort.setAttribute("position", `0 -2,850 ${56-((textPorts.indexOf(parseInt(portnumber))+1)*5)}`)
          valuePort.setAttribute("id", `portnumber${port.number}`);
          valuePort.setAttribute("align", "center")
          valuePort.setAttribute("rotation", "90 0 0");
          valuePort.setAttribute("color", "white");
          valuePort.setAttribute("scale", "15 15 1");
          board?.appendChild(valuePort)

         }

          
        })

      }
    })




  }




  private showInfoLink(event: any): void {
    //Declaracion de variables
    const distance: number = 3
    let loss: any
    let bandera: boolean = true
    let delay: any

    
    //Obtencion de elementos por ID
    const network = document.getElementById("network")
    const camara = document.getElementById("camara")
    const sky = document.getElementById("entorno")


    //Creacion de nuevos elementos
    const entorno = document.createElement('a-sky')

    //Destruccion del entorno
    sky?.remove()

    //Seteo de nuevos atributos
    entorno.setAttribute("id", "entorno")
    entorno?.setAttribute("src", 'assets/fondoLinks1.jpg')
    camara?.setAttribute("position", "350 0 350")
    camara?.setAttribute("rotation", "0 0 0")
    //camara?.setAttribute("position","5 0 0")


    //Agregar nuevo entorno
    network?.appendChild(entorno)


    //Obtencion de la poscion y rotacion de la camara
    const rotationS = camara?.getAttribute("rotation")
    const cameraRot = JSON.parse(JSON.stringify(rotationS))
    const cameraPos = JSON.parse(JSON.stringify(camara?.getAttribute("position")))
    const x = cameraPos.x + distance * Math.sin(cameraRot.y * (Math.PI / 180));
    const z = cameraPos.z - distance * Math.cos(cameraRot.y * (Math.PI / 180));

    //Creacion y seteo de los  del TV para visualizar los datos
    const board = document.createElement('a-obj-model');
    board.setAttribute('src', '#TV-obj');
    board.setAttribute('id', 'board');
    board.setAttribute('material', 'src:assets/TV.jpg');
    board.setAttribute('scale', '0.05 0.05 0.05');
    board.setAttribute("position", `${x} ${cameraPos.y - 1} ${z}`)

    board.setAttribute("rotation", "-90 0 0")
    network?.appendChild(board)

    //Creacion de la puerta de salida
    const puerta = document.createElement('a-obj-model');
    puerta.setAttribute('src', '#puerta-obj');
    puerta.setAttribute('material', 'src:assets/puerta.jpg');
    puerta.setAttribute('id', 'puerta')
    puerta.setAttribute('scale', '0.02 0.02 0.02');
    puerta.setAttribute("position", `${x} ${cameraPos.y + 1} ${z + 5}`)
    puerta.setAttribute("rotation", "90 0 0")
    puerta.addEventListener('click', () => { this.destroy() })
    network?.appendChild(puerta)



    //Obtencion del id del link al cual se esta mirando
    const linkId = event.target.getAttribute("id")

    /*Creacion,seteo del texto con el valor del link al cual se esta mirando 
      y agregar al TV de visulizacion */
    const text = document.createElement("a-text");
    text.setAttribute("value", `link ${linkId}`);
    text.setAttribute("id", `Link ${linkId}`);
    text.setAttribute("position", `0 -2,850 63`);
    text.setAttribute("align", "center");
    text.setAttribute("color", "white");
    text.setAttribute("scale", "30 30 1");
    text.setAttribute("rotation", "90 0 0");
    board?.appendChild(text)

    //Creacion,seteo y agregacion del texto con el titulo de las perdidas al TV de visulizacion
    const perdidas = document.createElement('a-text')
    perdidas.setAttribute("value", 'Perdidas')
    perdidas.setAttribute("id", 'Perdidas');
    perdidas.setAttribute("align", "center");
    perdidas.setAttribute("color", "red");
    perdidas.setAttribute("scale", "15 15 1");
    perdidas.setAttribute("rotation", "90 0 0");
    perdidas.setAttribute("position", `-27 -2,850 56`);
    board?.appendChild(perdidas)

    //Obtencion del valor de perdidas del enlace
    let [origen1, destino1] = linkId.split('-')
    const origen = origen1.replace('S', '')
    const destino = destino1.replace('S', '')

    //creacion del texto del valor de perdidas
    const valueperdidas = document.createElement('a-text')
    valueperdidas.setAttribute("id", 'Valor de Perdidas');
    valueperdidas.setAttribute("scale", "15 15 1");
    valueperdidas.setAttribute("rotation", "90 0 0");
    valueperdidas.setAttribute("position", `-30 -2,850 50`);

    loss = this.listLinks.find(link => link.origen == origen1 && link.destino == destino1)?.loss

    valueperdidas.setAttribute("value", `${loss}`);
    board.appendChild(valueperdidas)







    //Creacion,seteo y agregacion del texto con el titulo de <<delay>> al TV de visulizacion
    const textdelay = document.createElement('a-text')
    textdelay.setAttribute("value", 'Delay ')
    textdelay.setAttribute("id", 'Perdidas');
    textdelay.setAttribute("align", "center");
    textdelay.setAttribute("color", "red");
    textdelay.setAttribute("scale", "15 15 1");
    textdelay.setAttribute("rotation", "90 0 0");
    textdelay.setAttribute("position", `0 -2,850 56`);
    board?.appendChild(textdelay)

    //creacion del texto del valor de perdidas
    const valuedelay = document.createElement('a-text')
    valuedelay.setAttribute("id", 'Valor de Perdidas');
    valuedelay.setAttribute("scale", "15 15 1");
    valuedelay.setAttribute("rotation", "90 0 0");
    valuedelay.setAttribute("position", `-8 -2,850 50`);

    delay = this.listLinks.find(link => link.origen == origen1 && link.destino == destino1)?.delay
    console.log(delay)

    valuedelay.setAttribute("value", `${delay.toFixed(4)}ms`);
    board.appendChild(valuedelay)

    //Creacion,seteo y agregacion del texto con el titulo de delay al TV de visulizacion
    const textthorughput = document.createElement('a-text')
    textthorughput.setAttribute("value", 'Thorughput ')
    textthorughput.setAttribute("id", 'thorughput');
    textthorughput.setAttribute("align", "center");
    textthorughput.setAttribute("color", "red");
    textthorughput.setAttribute("scale", "15 15 1");
    textthorughput.setAttribute("rotation", "90 0 0");
    textthorughput.setAttribute("position", `30 -2,850 56`);
    board?.appendChild(textthorughput)

    //creacion del texto del valor de bw
    const valuethorughput = document.createElement('a-text')
    valuethorughput.setAttribute("id", 'Valor del thorughput');
    valuethorughput.setAttribute("scale", "15 15 1");
    valuethorughput.setAttribute("rotation", "90 0 0");
    valuethorughput.setAttribute("position", `24 -2,850 50`);
    let thorughput: any = this.listLinks.find(link => link.origen == origen1 && link.destino == destino1)
    let free_bw = parseFloat(thorughput.throughput)
    valuethorughput.setAttribute("value", `${free_bw.toFixed(4)}Kb/s`);
    board.appendChild(valuethorughput)


    //Peticion y actualizacion de los valores 
    const interval = setInterval(() => {
      if (!bandera) {
        clearInterval(interval)
        return
      }
      this.Topologia.getMetrics(origen, destino).subscribe({

        next: (data) => {

          loss = data.perdidas; // Ajusta según la estructura de respuesta
          delay = parseFloat(data.delay.replace('ms', ''))
          thorughput = (parseFloat(data.throughput) / 1000)

          valueperdidas.setAttribute("value", `${loss}%`);
          valuedelay.setAttribute("value", `${delay.toFixed(4)}ms`);
          valuethorughput.setAttribute("value", `${thorughput.toFixed(4)}Kb/s`);
          if (!document.getElementById("board")) {
            bandera = false;
          }
        },
        error: (error) => {
          console.error("Error al obtener pérdidas:", error);
          valueperdidas.setAttribute("value", `error`);
        }
      });
    }, 2000)

  }

  private destroy(): void {
    //Obtencion de elementos por ID

    const network = document.getElementById("network")
    const camara = document.getElementById("camara")
    const sky = document.getElementById("entorno")
    const board = document.getElementById("board")
    const puerta = document.getElementById("puerta")

    //Creacion de nuevos elementos
    const entorno = document.createElement('a-sky')

    //Destruccion del entorno
    sky?.remove()
    board?.remove()
    puerta?.remove()

    //Seteo de nuevos atributos
    entorno.setAttribute("id", "entorno")
    entorno?.setAttribute("src", 'assets/fondo1.jpg')
    camara?.setAttribute("position", "0 3 13")

    camara?.setAttribute("rotation", "0 0 0")


    //Agregar nuevo entorno
    network?.appendChild(entorno)



  }

  private procesarICMPMensaje(mensaje: any): Array<ICMP> {
    // Asegurarse de que el mensaje sea un objeto
    if (typeof mensaje === 'string') {
      try {
        mensaje = JSON.parse(mensaje); // Convertir JSON string a objeto
      } catch (error) {
        console.error('Error al parsear el mensaje:', error);
        return this.packets; // Retornar el array actual sin modificar
      }
    }

    // Validar que el mensaje tenga las propiedades necesarias
    if ('src_ip' in mensaje && 'dst_ip' in mensaje && 'icmp_type' in mensaje && 'icmp_code' in mensaje) {
      // Crear un objeto que cumpla con la interfaz ICMP
      const icmpPacket: ICMP = {
        src_ipv4: mensaje.src_ip,
        dst_ipv4: mensaje.dst_ip,
        icmp_type: mensaje.icmp_type,
        icmp_code: mensaje.icmp_code,
        RTT: mensaje.RTT
      };

      // Añadir al array de packets
      this.packets.push(icmpPacket);
    } else {
      console.warn('El mensaje recibido no tiene las propiedades necesarias:', mensaje);
    }

    // Retornar el array de packets actualizado
    this.getDelayNetwork(mensaje.RTT)
    return this.packets;
  }





  private renderPackets(packets: Array<ICMP>): void {
    packets.forEach((packet) => {
      const src_ip = `["${packet.src_ipv4}"]`;
      const dst_ip = `["${packet.dst_ipv4}"]`;

      const sourceEl = this.listHost.find(host => host.IP == src_ip)

      const targetEl = this.listHost.find(host => host.IP == dst_ip)

      if (sourceEl && targetEl) {
        const sourcePos = this.coordenadasHost.find(coordenada => coordenada.dpid = sourceEl.HostDPID)
        const targetPos = this.coordenadasHost.find(coordenada => coordenada.dpid = targetEl.HostDPID)


        const packetEl = document.createElement('a-entity');
        packetEl.setAttribute('geometry', 'primitive: sphere; radius: 0.2');
        packetEl.setAttribute('material', 'color: yellow');
        packetEl.setAttribute('position', `${sourcePos?.X} ${sourcePos?.Y} ${sourcePos?.Z}`);
        packetEl.setAttribute("id", "lalalal")
        setTimeout(() => {
          packetEl.setAttribute('animation', `
                property: position;
                to: ${targetPos?.X} ${targetPos?.Y} ${targetPos?.Z};
                dur: 200s0;
                easing: easeInOutQuad;
            `);
        }, 10); // Pequeño retraso para asegurar la inicialización


        // Eliminar el paquete después de la animación
        packetEl.addEventListener('animationcomplete', () => {
          packetEl.parentElement?.removeChild(packetEl);
        });


        const plane = document.getElementById("network");
        plane?.appendChild(packetEl);
      }
    });



  }




}
