document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("click", (e) => {
        const btn = e.target.closest(".product-result");
        if (!btn) return;

        const titleInput = document.getElementById("id_title");
        const imageInput = document.getElementById("id_image_url");

        if (titleInput) {
            const textNodes = Array.from(btn.childNodes).filter(node => node.nodeType === Node.TEXT_NODE);
            const productName = textNodes.map(n => n.textContent).join("").trim();
            if (productName) titleInput.value = productName;
        }

        const productSearchContainer = document.querySelector("[data-product-target='community']");
        if (productSearchContainer && imageInput) {
            const toastBox= document.querySelector("#feedback");
            if (toastBox) {
                toastBox.textContent = "Data produk Open Food Facts berhasil disematkan.";
                toastBox.hidden = false;
                setTimeout(() => { toastBox.hidden = true; }, 4000);
            }
        }
    });

    const mapElement = document.getElementById("map-picker");
    if (!mapElement) return;

    const latInput = document.getElementById("id_latitude");
    const lngInput = document.getElementById("id_longitude");
    const locationInput = document.getElementById("id_pickup_location");
    const coordsDisplay = document.getElementById("coords-display");

    const initialLat = (latInput && latInput.value) ? parseFloat(latInput.value.replace(",", ".")) : -6.3627;
    const initialLng = (lngInput && lngInput.value) ? parseFloat(lngInput.value.replace(",", ".")) : 106.8271;

    const map = L.map("map-picker").setView([initialLat, initialLng], 14);

    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}", {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, TomTom',
        maxZoom: 19
    }).addTo(map);

    let marker = L.marker([initialLat, initialLng], { draggable: true }).addTo(map);

    function updateCoordinates(lat, lng) {
        latInput.value = lat.toFixed(6);
        lngInput.value = lng.toFixed(6);
        if (coordsDisplay) {
            coordsDisplay.textContent = "Koordinat terpilih: " + lat.toFixed(5) + ", " + lng.toFixed(5);
        }
    }

    marker.on("dragend", function(e) {
        const position = marker.getLatLng();
        updateCooordinates(position.lat, position.lng);
    });

    map.on("click", function (e) {
        marker.setLatLng(e.latlng);
        updateCoordinates(e.latlng.lat, e.latlng.lng);
    });

    if (!latInput.value || !lngInput.value) {
        updateCoordinates(initialLat, initialLng);
    }
});