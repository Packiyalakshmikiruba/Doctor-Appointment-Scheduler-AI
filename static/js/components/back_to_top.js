//==========================================
// BACK TO TOP
//==========================================

document.addEventListener("DOMContentLoaded",()=>{

const btn=document.getElementById("backToTop");

if(!btn) return;

// Show Button

window.addEventListener("scroll",()=>{

if(window.scrollY>250){

btn.classList.add("show");

}else{

btn.classList.remove("show");

}

});

// Scroll Top

btn.addEventListener("click",()=>{

window.scrollTo({

top:0,

behavior:"smooth"

});

});

});

// Floating Animation

setInterval(()=>{

const btn=document.getElementById("backToTop");

if(btn && btn.classList.contains("show")){

btn.animate([

{

transform:"translateY(0px)"

},

{

transform:"translateY(-5px)"

},

{

transform:"translateY(0px)"

}

],{

duration:1800

});

}

},2200);