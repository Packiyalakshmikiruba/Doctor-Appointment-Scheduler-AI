// ======================================
// QUICK ACCESS BAR
// ======================================

document.addEventListener("DOMContentLoaded",function(){

const cards=document.querySelectorAll(".quick-card");

cards.forEach((card,index)=>{

card.style.opacity="0";
card.style.transform="translateY(25px)";

setTimeout(()=>{

card.style.transition=".45s";

card.style.opacity="1";

card.style.transform="translateY(0px)";

},120*index);

});

});

// Ripple Effect

document.querySelectorAll(".quick-card").forEach(card=>{

card.addEventListener("click",function(e){

const ripple=document.createElement("span");

const rect=this.getBoundingClientRect();

const size=Math.max(rect.width,rect.height);

ripple.style.width=size+"px";
ripple.style.height=size+"px";

ripple.style.left=(e.clientX-rect.left-size/2)+"px";
ripple.style.top=(e.clientY-rect.top-size/2)+"px";

ripple.style.position="absolute";
ripple.style.borderRadius="50%";
ripple.style.background="rgba(255,255,255,.45)";
ripple.style.transform="scale(0)";
ripple.style.animation="quickRipple .6s linear";
ripple.style.pointerEvents="none";

this.appendChild(ripple);

setTimeout(()=>{

ripple.remove();

},600);

});

});

// Ripple Animation

const style=document.createElement("style");

style.innerHTML=`

@keyframes quickRipple{

to{

transform:scale(4);

opacity:0;

}

}

.quick-card{

overflow:hidden;

position:relative;

}

`;

document.head.appendChild(style);