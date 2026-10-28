document.addEventListener("DOMContentLoaded", () => {
    // 1. Tampilkan Peta Titik Jemput Esri
    const mapElement = document.getElementById("detail-map");
    if (mapElement) {
        const rawLat = (mapElement.dataset.lat || "-6.3627").replace(",", ".");
        const rawLng = (mapElement.dataset.lng || "106.8271").replace(",", ".");
        const lat = parseFloat(rawLat);
        const lng = parseFloat(rawLng);
        const title = mapElement.dataset.title || "Titik Penjemputan";

        const map = L.map("detail-map").setView([lat, lng], 15);

        L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
            attribution: 'Tiles &copy; Esri',
            maxZoom: 19
        }).addTo(map);

        L.marker([lat, lng]).addTo(map)
            .bindPopup("<strong>" + title + "</strong><br>Titik penjemputan makanan.")
            .openPopup();
    }

    // 2. Transaksi Klaim Porsi Makanan via AJAX (Dengan Debug Logging)
    const claimForm = document.getElementById("claim-food-form");
    if (claimForm) {
        claimForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = claimForm.querySelector("button[type='submit']");
            submitBtn.disabled = true;
            submitBtn.textContent = "Memproses...";

            const url = claimForm.action;
            const formData = new FormData(claimForm);
            const csrfToken = formData.get("csrfmiddlewaretoken");

            console.log("Mengirim request ke URL:", url);

            try {
                const response = await fetch(url, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": csrfToken,
                    }
                });

                console.log("Status respons server:", response.status);

                const responseText = await response.text();
                let data;
                try {
                    data = JSON.parse(responseText);
                } catch {
                    console.error("Server tidak mengembalikan JSON, respons mentah:", responseText);
                    alert("Server mengembalikan error (Status " + response.status + "). Cek tab Network / Console.");
                    return;
                }

                if (!response.ok) {
                    alert(data.error || "Gagal memproses klaim.");
                    return;
                }

                // Perbarui sisa porsi dan kontak secara dinamis di antarmuka
                const remainingBadge = document.getElementById("remaining-badge");
                if (remainingBadge) {
                    remainingBadge.textContent = data.remaining_portions + " Porsi Tersedia";
                }
                
                const contactContainer = document.getElementById("contact-section");
                if (contactContainer && data.contact_info) {
                    contactContainer.innerHTML = 
                        '<div class="contact-box">' +
                            '<strong>Kontak Penjemputan:</strong><br>' +
                            data.contact_info +
                        '</div>';
                }

                claimForm.reset();
                alert(data.message);

                if (data.remaining_portions <= 0) {
                    claimForm.style.display = "none";
                }
            } catch (err) {
                console.error("Detail error fetch:", err);
                alert("Detail galat koneksi: " + err.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = "Ajukan Klaim Porsi";
            }
        });
    }
});