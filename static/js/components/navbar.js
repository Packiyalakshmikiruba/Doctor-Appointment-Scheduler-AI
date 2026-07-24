/* ==========================================================
   AI HOSPITAL NAVBAR
========================================================== */

document.addEventListener("DOMContentLoaded", function () {

    const navbar = document.querySelector(".hospital-navbar");

    const collapse = document.getElementById("mainNavbar");

    const navLinks = document.querySelectorAll(".nav-link");

    /* ==========================================
       Navbar Scroll Effect
    ========================================== */

    function navbarScroll() {

        if (window.scrollY > 20) {

            navbar.classList.add("scrolled");

        } else {

            navbar.classList.remove("scrolled");

        }

    }

    navbarScroll();

    window.addEventListener("scroll", navbarScroll);

    /* ==========================================
       Active Menu Animation
    ========================================== */

    navLinks.forEach(link => {

        link.addEventListener("click", function () {

            navLinks.forEach(item => {

                item.classList.remove("active");

            });

            this.classList.add("active");

        });

    });

    /* ==========================================
       Auto Close Navbar On Mobile
    ========================================== */

    if (collapse) {

        navLinks.forEach(link => {

            link.addEventListener("click", () => {

                if (window.innerWidth < 1200) {

                    const bsCollapse = bootstrap.Collapse.getInstance(collapse);

                    if (bsCollapse) {

                        bsCollapse.hide();

                    }

                }

            });

        });

    }

    /* ==========================================
       Dropdown Hover (Desktop)
    ========================================== */

    if (window.innerWidth > 1199) {

        document.querySelectorAll(".dropdown").forEach(drop => {

            drop.addEventListener("mouseenter", function () {

                const menu = this.querySelector(".dropdown-menu");

                if (menu) {

                    menu.classList.add("show");

                }

            });

            drop.addEventListener("mouseleave", function () {

                const menu = this.querySelector(".dropdown-menu");

                if (menu) {

                    menu.classList.remove("show");

                }

            });

        });

    }

    /* ==========================================
       Search Button Animation
    ========================================== */

    const searchBtn = document.querySelector(".search-btn");

    if (searchBtn) {

        searchBtn.addEventListener("mouseenter", () => {

            searchBtn.style.transform = "scale(1.08)";

        });

        searchBtn.addEventListener("mouseleave", () => {

            searchBtn.style.transform = "scale(1)";

        });

    }

    /* ==========================================
       Notification Animation
    ========================================== */

    const notify = document.querySelector(".notification-btn");

    if (notify) {

        setInterval(() => {

            notify.animate(

                [

                    { transform: "rotate(0deg)" },

                    { transform: "rotate(-12deg)" },

                    { transform: "rotate(12deg)" },

                    { transform: "rotate(0deg)" }

                ],

                {

                    duration: 700

                }

            );

        }, 10000);

    }

    /* ==========================================
       Profile Hover
    ========================================== */

    const profile = document.querySelector(".profile-btn");

    if (profile) {

        profile.addEventListener("mouseenter", () => {

            profile.style.boxShadow =

                "0 10px 25px rgba(37,99,235,.25)";

        });

        profile.addEventListener("mouseleave", () => {

            profile.style.boxShadow =

                "none";

        });

    }

    /* ==========================================
       Ripple Effect
    ========================================== */

    document.querySelectorAll(".nav-link").forEach(button => {

        button.addEventListener("click", function (e) {

            const ripple = document.createElement("span");

            ripple.classList.add("ripple");

            const rect = button.getBoundingClientRect();

            ripple.style.left = (e.clientX - rect.left) + "px";

            ripple.style.top = (e.clientY - rect.top) + "px";

            this.appendChild(ripple);

            setTimeout(() => {

                ripple.remove();

            }, 600);

        });

    });

});