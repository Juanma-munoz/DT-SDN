import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class GetTopologiaService {

  constructor(private http :HttpClient ) {}
  private URISwitches="http://localhost:3000/switches"
  private URIHosts="http://localhost:3000/hosts"
  private URILinks="http://localhost:3000/links"
  private URILoss="http://localhost:3000/metrics"
  getSwitches():Observable<any> {
    return this.http.get(this.URISwitches); 
  }

  getHosts():Observable<any> {
    return this.http.get(this.URIHosts); 
  }
  getLinks():Observable<any> {
    return this.http.get(this.URILinks); 
  }
  getMetrics(origen:string,destino:string):Observable<any> {
    const url = `${this.URILoss}/?origen=${origen}&destino=${destino}`;
    return this.http.get(url); 
  }

}
