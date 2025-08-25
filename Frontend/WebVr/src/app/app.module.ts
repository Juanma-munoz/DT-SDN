import { CUSTOM_ELEMENTS_SCHEMA, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './components/root/app.component';
import { HttpClientModule } from '@angular/common/http';
import { SwitchesComponent } from './components/switches/switches.component';
import { HomeComponent } from './components/home/home/home.component';
import { HostsComponent } from './components/hosts/hosts/hosts.component';


@NgModule({
  declarations: [
    AppComponent,
    SwitchesComponent,
    HomeComponent,
    HostsComponent,
    
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule, 
    
  
  ],
  providers: [],
  bootstrap: [AppComponent],
  schemas:[CUSTOM_ELEMENTS_SCHEMA]
})
export class AppModule { }
