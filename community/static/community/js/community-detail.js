document.addEventListener("DOMContentLoaded", () => {
    const mapElement = document.getElementById("detail-map");
    if (mapElement) {
        const lat = parseFloat(mapElement.dataset.lat || "-6.3627");
        const lng = parseFloat(mapElement.dataset.lng  || "106.8271");
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

    const claimForm = document.getElementById("claim-food-form");
    if (claimForm) {
        claimForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = claimForm.querySelector("button[type='submit']");
            submitBtn.disabled = true;
            submitBtn.textContent = "Memproses...";

            const url = claimForm.action;
            const formData = new FormData(claimForm);
            
            try {
                const response = await fetch(urll, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    }
                });
                const data = await response.json();

                if (!response.ok) {
                    alert(data.error || "Gagal memproses klaim.");
                    submitBtn.disabled = false;
                    submitBtn.textContent = "Ajukan Klaim Porsi";
                    return;
                }

                const remainingBadge = document.getElementById("remaining-badge");
                if (remainingBadge) {
                    remainingBadge.textContent = data.remaining_portions + " Porsi Tersedia";
                }

                const contactContainer = document.getElementById("contact-section");
                if (contactContainer && data.contact_info) {
                    contactContainer.innerHTML = '<div class="contact-box">' + '<strong>Kontak Penjemputan:</strong><br>' + data.contact_info + '</div>'; 
                }

                claimForm.requestFullscreen();
                alert(data.message);

                if (data.remaining_portions <= 0) {
                    claimForm.style.display = "none";
                }
            } catch (err) {
                alert("Terjadi kesalahan jaringan. Silakan coba lagi.");
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = "Ajukan Klaim Porsi";
            }
        });
    }
});