(function(){

    const footer=document.querySelector(".footer-section");

    if(!footer) return;

    const observer=new IntersectionObserver(function(entries){

        entries.forEach(function(entry){

            if(entry.isIntersecting){

                footer.classList.add("footer-visible");

            }

        });

    },{

        threshold:.2

    });

    observer.observe(footer);

})();