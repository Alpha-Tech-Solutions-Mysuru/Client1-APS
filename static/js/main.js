document.addEventListener("DOMContentLoaded", function () {

    const alerts = document.querySelectorAll(".alert");
    const toasts = document.querySelectorAll(".app-message-toast");

    toasts.forEach(function (toast) {

        bootstrap.Toast.getOrCreateInstance(toast).show();

    });

    alerts.forEach(function (alert) {

        setTimeout(function () {

            let bsAlert = bootstrap.Alert.getOrCreateInstance(alert);

            bsAlert.close();

        }, 4000);

    });

});
