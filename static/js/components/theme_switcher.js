//==========================================
// THEME SWITCHER
//==========================================

document.addEventListener("DOMContentLoaded",()=>{

const btn=document.getElementById("themeToggle");

const icon=document.getElementById("themeIcon");

// Previous Theme

if(localStorage.getItem("theme")==="dark"){

document.body.classList.add("dark-mode");

icon.className="fas fa-sun";

}

// Click

btn.addEventListener("click",()=>{

document.body.classList.toggle("dark-mode");

if(document.body.classList.contains("dark-mode")){

icon.className="fas fa-sun";

localStorage.setItem("theme","dark");

}else{

icon.className="fas fa-moon";

localStorage.setItem("theme","light");

}

});

});