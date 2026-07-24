// ======================================
// AI GREETING POPUP
// ======================================

document.addEventListener("DOMContentLoaded",()=>{

const popup=document.getElementById("aiGreetingPopup");

const close=document.getElementById("closeGreeting");

const start=document.getElementById("startChatBtn");

// Show after 2 seconds

setTimeout(()=>{

popup.style.display="block";

},2000);

// Close

close.addEventListener("click",()=>{

popup.style.display="none";

});

// Open Chat

start.addEventListener("click",()=>{

popup.style.display="none";

const modal=document.getElementById("chatModal")

|| document.getElementById("liveChatModal");

if(modal){

const bsModal=new bootstrap.Modal(modal);

bsModal.show();

}

});

// Auto Hide

setTimeout(()=>{

popup.style.display="none";

},15000);

});