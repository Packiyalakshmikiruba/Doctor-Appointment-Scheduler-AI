// ======================================
// AI GREETING POPUP
// ======================================

document.addEventListener("DOMContentLoaded", () => {

    const popup = document.getElementById("aiGreetingPopup");
    const close = document.getElementById("closeGreeting");
    const start = document.getElementById("startChatBtn");

    if (!popup) return;

    // ======================================
    // Show only once per browser tab
    // ======================================

    if (!sessionStorage.getItem("aiGreetingShown")) {

        setTimeout(() => {

            popup.style.display = "block";

            sessionStorage.setItem("aiGreetingShown", "true");

        }, 2000);

    }

    // ======================================
    // Close Popup
    // ======================================

    if (close) {

        close.addEventListener("click", () => {

            popup.style.display = "none";

        });

    }

    // ======================================
    // Open Chat
    // ======================================

    if (start) {

        start.addEventListener("click", () => {

            popup.style.display = "none";

            const modal =
                document.getElementById("chatModal") ||
                document.getElementById("liveChatModal");

            if (modal) {

                const bsModal = new bootstrap.Modal(modal);

                bsModal.show();

            }

        });

    }

    // ======================================
    // Auto Hide after 15 sec
    // ======================================

    setTimeout(() => {

        popup.style.display = "none";

    }, 15000);

});