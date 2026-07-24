// ======================================
// FLOATING CHAT
// ======================================

document.addEventListener("DOMContentLoaded",()=>{

const btn=document.getElementById("chatToggle");

if(!btn) return;

btn.addEventListener("mouseenter",()=>{

btn.style.transform="translateY(-8px) scale(1.08)";

});

btn.addEventListener("mouseleave",()=>{

btn.style.transform="translateY(0px) scale(1)";

});

btn.addEventListener("click",()=>{

// Existing Chat Modal

const modal=document.getElementById("chatModal") ||

document.getElementById("liveChatModal");

if(modal){

const bsModal=new bootstrap.Modal(modal);

bsModal.show();

}

});

});

// Floating animation

setInterval(()=>{

const btn=document.getElementById("chatToggle");

if(btn){

btn.animate([

{

transform:"translateY(0px)"

},

{

transform:"translateY(-6px)"

},

{

transform:"translateY(0px)"

}

],{

duration:1800

});

}

},2500);