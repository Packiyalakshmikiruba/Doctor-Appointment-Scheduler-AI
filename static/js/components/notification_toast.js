//==========================================
// NOTIFICATION TOAST
//==========================================

document.addEventListener("DOMContentLoaded", () => {

    const toastElement = document.getElementById("notificationToast");

    if (!toastElement) return;

    const toast = new bootstrap.Toast(toastElement);

    window.showNotification = function (title, message) {

        document.getElementById("notifyTitle").innerHTML = title;
        document.getElementById("notifyMessage").innerHTML = message;
        document.getElementById("notifyTime").innerHTML = "Just Now";

        toast.show();
    };

    //==========================================
    // Show Welcome Notification Only Once
    //==========================================

    if (!sessionStorage.getItem("welcome_notification_shown")) {

        setTimeout(() => {

            showNotification(
                "Welcome 👋",
                "Welcome to AI Hospital Management System."
            );

            sessionStorage.setItem("welcome_notification_shown", "true");

        }, 2500);

    }

});