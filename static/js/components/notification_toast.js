//==========================================
// NOTIFICATION TOAST
//==========================================

document.addEventListener("DOMContentLoaded",()=>{

const toastElement=document.getElementById("notificationToast");

if(!toastElement) return;

const toast=new bootstrap.Toast(toastElement);

window.showNotification=function(title,message){

document.getElementById("notifyTitle").innerHTML=title;

document.getElementById("notifyMessage").innerHTML=message;

document.getElementById("notifyTime").innerHTML="Just Now";

toast.show();

};

// Demo Welcome Notification

setTimeout(()=>{

showNotification(

"Welcome 👋",

"Welcome to AI Hospital Management System."

);

},2500);

});