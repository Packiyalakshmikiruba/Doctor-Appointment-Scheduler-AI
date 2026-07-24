//==========================================
// GLOBAL SEARCH
//==========================================

document.addEventListener("DOMContentLoaded",()=>{

const input=document.getElementById("globalSearchInput");

const cards=document.querySelectorAll(".search-card");

const results=document.getElementById("searchResults");

if(!input) return;

// Live Search

input.addEventListener("keyup",function(){

const keyword=this.value.toLowerCase();

let html="";

let found=0;

cards.forEach(card=>{

const text=card.innerText.toLowerCase();

if(text.includes(keyword) && keyword!==""){

found++;

html+=`

<div class="search-item"
onclick="window.location='${card.href}'">

${card.innerHTML}

</div>

`;

}

});

if(keyword===""){

results.style.display="none";

results.innerHTML="";

return;

}

results.style.display="block";

if(found===0){

results.innerHTML=`

<div class="text-center text-muted p-4">

<i class="fas fa-search fa-2x mb-3"></i>

<br>

No Results Found

</div>

`;

}else{

results.innerHTML=html;

}

});

// Ctrl + K

document.addEventListener("keydown",function(e){

if(e.ctrlKey && e.key.toLowerCase()=="k"){

e.preventDefault();

const modal=new bootstrap.Modal(

document.getElementById("globalSearchModal")

);

modal.show();

setTimeout(()=>{

input.focus();

},300);

}

});

// /

document.addEventListener("keydown",function(e){

if(e.key=="/" && document.activeElement.tagName!="INPUT"){

e.preventDefault();

const modal=new bootstrap.Modal(

document.getElementById("globalSearchModal")

);

modal.show();

setTimeout(()=>{

input.focus();

},300);

}

});

});