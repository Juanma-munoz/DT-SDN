
AFRAME.registerComponent('gotoswtich',{
    schema: {
        data: { type: 'string', default: '' }, 
      },
    init: function(){
        this.el.addEventListener('click',()=>{
        console.log("Estas mirando al switch")
        const camara=document.getElementById("camara")
        camara.setAttribute("position",'100 0 0')


        const entorno=document.getElementById("entorno")
        entorno.setAttribute("visible",'false')

        //window.location.assign('/switches')  
     })   
    }
    
})



AFRAME.registerComponent('gotohosts',{
  schema: {
      data: { type: 'string', default: '' }, 
    },
  init: function(){
      this.el.addEventListener('click',()=>{
      console.log("Estas mirando al switch")
      window.location.assign('/hosts')  
   })   
  }
  
})
