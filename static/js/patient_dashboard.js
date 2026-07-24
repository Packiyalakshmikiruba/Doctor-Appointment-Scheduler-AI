function updateClock(){

    const now = new Date();

    const time = now.toLocaleTimeString();

    const date = now.toDateString();

    const liveTime = document.getElementById("liveTime");
    const liveDate = document.getElementById("liveDate");

    if(liveTime){
        liveTime.innerHTML = time;
    }

    if(liveDate){
        liveDate.innerHTML = date;
    }

}

updateClock();

setInterval(updateClock,1000);
const messageModal=document.getElementById("messageModal");

if(messageModal){

messageModal.addEventListener("shown.bs.modal",function(){

console.log("Chat Opened");

});

}
const countdown=document.getElementById("countdown");

if(countdown){

    const target=new Date(countdown.dataset.time);

    function update(){

        const now=new Date();

        const diff=target-now;

        if(diff<=0){

            countdown.innerHTML="Started";

            return;

        }

        const d=Math.floor(diff/86400000);

        const h=Math.floor((diff%86400000)/3600000);

        const m=Math.floor((diff%3600000)/60000);

        const s=Math.floor((diff%60000)/1000);

        countdown.innerHTML=`${d}d ${h}h ${m}m ${s}s`;

    }

    update();

    setInterval(update,1000);

}
// ================================
// Appointment Chart
// ================================

new Chart(

document.getElementById("appointmentChart"),

{

type:"line",

data:{

labels:["Jan","Feb","Mar","Apr","May","Jun"],

datasets:[{

label:"Appointments",

data:[3,5,4,6,2,7],

borderWidth:3,

fill:false

}]

}

}

);

// ================================
// Payment Chart
// ================================

new Chart(

document.getElementById("paymentChart"),

{

type:"bar",

data:{

labels:["Paid","Pending"],

datasets:[{

data:[{{ total_paid }},{{ total_due }}]

}]

}

}

);

// ================================
// Bills
// ================================

new Chart(

document.getElementById("billChart"),

{

type:"doughnut",

data:{

labels:["Paid","Pending"],

datasets:[{

data:[

{{ payments.count }},

{{ pending_bills.count }}

]

}]

}

}

);

// ================================
// Medical
// ================================

new Chart(

document.getElementById("medicalChart"),

{

type:"pie",

data:{

labels:[

"Medical Records",

"Prescriptions"

],

datasets:[{

data:[

{{ stats.medical_records }},

{{ stats.prescriptions }}

]

}]

}

}

);
const btn=document.getElementById("darkModeBtn");

if(btn){

btn.onclick=function(){

document.body.classList.toggle("dark-mode");

}

}
const topBtn=document.getElementById("topBtn");

window.onscroll=function(){

if(document.documentElement.scrollTop>200){

topBtn.style.display="block";

}

else{

topBtn.style.display="none";

}

}

topBtn.onclick=function(){

window.scrollTo({

top:0,

behavior:"smooth"

});

}

