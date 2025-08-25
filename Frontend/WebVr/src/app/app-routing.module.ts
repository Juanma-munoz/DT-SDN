import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AppComponent } from './components/root/app.component';
import { SwitchesComponent } from './components/switches/switches.component';
import { HomeComponent } from './components/home/home/home.component';
import { HostsComponent } from './components/hosts/hosts/hosts.component';

const routes: Routes = [
  {path:'',redirectTo:'home',pathMatch:'full'},
  {path:'switches',component:SwitchesComponent},
  {path:'home',component:HomeComponent},
  {path:'hosts',component:HostsComponent}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
