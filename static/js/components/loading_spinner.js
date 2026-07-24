//==========================================
// PAGE LOADER
//==========================================

window.addEventListener("load",function(){

const loader=document.getElementById("pageLoader");

setTimeout(()=>{

loader.classList.add("loader-hide");

setTimeout(()=>{

loader.style.display="none";

},600);

},800);

});

// Show loader before page navigation

document.addEventListener("DOMContentLoaded",()=>{

document.querySelectorAll("a").forEach(link=>{

if(

link.target!== "_blank"

&&
!link.href.includes("#")

){

link.addEventListener("click",()=>{

const loader=document.getElementById("pageLoader");

if(loader){

loader.style.display="flex";

loader.classList.remove("loader-hide");

}

});

}

});

});