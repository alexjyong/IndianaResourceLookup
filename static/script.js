let trusteeData = [];
let foodPantryData = [];
let countyData = [];
let map;
let markers = [];

$(document).ready(function() {
    const countySelect = $('#countySelect');
    const filterSelect = $('#filterSelect');
    const addressForm = $('#addressForm');
    const addressInput = $('#addressInput');
    const resultsDiv = $('#results'); // Define resultsDiv here

    // Add default option to county select
    countySelect.append(`<option value="" selected>Select a county</option>`);

    fetch('static/utilities/data/counties_bounding_boxes.json')
        .then(response => response.json())
        .then(data => {
            countyData = data;
            data.forEach(county => {
                countySelect.append(`<option value="${county.name}">${county.name}</option>`);
            });
        })
        .catch(error => console.error('Error loading counties:', error));

    countySelect.change(function() {
        const selectedCounty = $(this).val();
        const selectedFilter = filterSelect.val();
        displayResults(selectedCounty, selectedFilter);
        updateMap(selectedCounty, selectedFilter);
    });

    filterSelect.change(function() {
        const selectedCounty = countySelect.val();
        const selectedFilter = $(this).val();
        displayResults(selectedCounty, selectedFilter);
        updateMap(selectedCounty, selectedFilter);
    });

    fetch('static/utilities/data/indiana_township_trustees.json')
        .then(response => response.json())
        .then(data => {
            trusteeData = data;
        })
        .catch(error => console.error('Error loading trustee data:', error));

    fetch('static/utilities/data/indiana_food_pantries.json')
        .then(response => response.json())
        .then(data => {
            foodPantryData = data;
        })
        .catch(error => console.error('Error loading food pantry data:', error));

    addressForm.submit(function(event) {
        event.preventDefault();
        const address = addressInput.val();
        if (address) {
            fetch(`/geocode?address=${encodeURIComponent(address)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.trustee) {
                        const trustee = data.trustee;
                        const county = data.county;
                        const township = data.township;

                        // Clear existing markers
                        markers.forEach(marker => map.removeLayer(marker));
                        markers = [];

                        // Add trustee marker
                        const marker = L.marker([trustee.Latitude, trustee.Longitude], { icon: trusteeIcon }).addTo(map);
                        marker.bindPopup(createPopupContent(trustee, 'Trustee'));
                        markers.push(marker);

                        // Zoom to the trustee location and open the popup
                        map.setView([trustee.Latitude, trustee.Longitude], 12);
                        marker.openPopup();

                        // Update results
                        resultsDiv.empty();
                        resultsDiv.append(createCard(trustee, 'Trustee'));

                    } else if (data.county) {
                        alert(`No immediate trustee found for your address in ${data.county}. Showing other results in that area.`);
                        countySelect.val(data.county).change();
                    } else {
                        alert('Address not found or invalid');
                    }
                })
                .catch(error => console.error('Error geocoding address:', error));
        }
    });

    initializeMap();
});

function initializeMap() {
    map = L.map('map').setView([40.2672, -86.1349], 7); // Centered on Indiana
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

const trusteeIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const foodPantryIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

function updateMap(county, filter) {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    const countyInfo = countyData.find(c => c.name === county);
    if (countyInfo) {
        const bbox = countyInfo.bbox;
        const bounds = [[bbox.southwest.lat, bbox.southwest.lng], [bbox.northeast.lat, bbox.northeast.lng]];
        map.fitBounds(bounds);
    }

    if (filter === 'all' || filter === 'trustee') {
        const trustees = trusteeData.filter(item => item.County === county);
        trustees.forEach(trustee => {
            const marker = L.marker([trustee.Latitude, trustee.Longitude], { icon: trusteeIcon }).addTo(map);
            marker.bindPopup(createPopupContent(trustee, 'Trustee'));
            markers.push(marker);
        });
    }

    if (filter === 'all' || filter === 'food_pantry') {
        const foodPantries = foodPantryData.filter(item => item.County === county);
        foodPantries.forEach(foodPantry => {
            const marker = L.marker([foodPantry.Latitude, foodPantry.Longitude], { icon: foodPantryIcon }).addTo(map);
            marker.bindPopup(createPopupContent(foodPantry, 'Food Pantry'));
            markers.push(marker);
        });
    }

    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}

function createPopupContent(data, type) {
    const directionsLink = data.Address ? 
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(data.Address)}" target="_blank">Get Directions</a>` : 
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${data.Latitude},${data.Longitude}" target="_blank">Get Directions</a>`;

    return `
        <strong>${data.Name} (${type})</strong><br>
        <strong>Address:</strong> ${data.Address}<br>
        <strong>Phone:</strong> <a href="tel:${data.Phone}">${data.Phone}</a><br>
        <strong>Website:</strong> ${data.Website && data.Website !== "N/A" ? `<a href="${data.Website}" target="_blank">${data.Website}</a>` : 'No website available'}<br>
        <strong>Hours:</strong><br>
        <ul>${data.Hours ? data.Hours.map(hour => `<li>${hour}</li>`).join('') : 'No open hours information available'}</ul>
        ${directionsLink}<br>
        <a href="#" class="report-link" data-name="${data.Name}" data-toggle="modal" data-target="#reportModal">Report Bad Information</a>
    `;
}

function displayResults(county, filter) {
    const resultsDiv = $('#results');
    resultsDiv.empty();

    if (filter === 'all' || filter === 'trustee') {
        const trustees = trusteeData.filter(item => item.County === county);
        trustees.forEach(trustee => {
            resultsDiv.append(createCard(trustee, 'Trustee'));
        });
    }

    if (filter === 'all' || filter === 'food_pantry') {
        const foodPantries = foodPantryData.filter(item => item.County === county);
        foodPantries.forEach(foodPantry => {
            resultsDiv.append(createCard(foodPantry, 'Food Pantry'));
        });
    }

    // Add event listener for report links
    $('.report-link').on('click', function() {
        const locationName = $(this).data('name');
        $('#location').val(locationName);
    });
}

function createCard(data, type) {
    const directionsLink = data.Address ? 
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(data.Address)}" target="_blank">Get Directions</a>` : 
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${data.Latitude},${data.Longitude}" target="_blank">Get Directions</a>`;

    return `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">${data.Name} (${type})</h5>
                <p class="card-text">
                    <strong>Address:</strong> ${data.Address}<br>
                    <strong>Phone:</strong> <a href="tel:${data.Phone}">${data.Phone}</a><br>
                    <strong>Website:</strong> ${data.Website && data.Website !== "N/A" ? `<a href="${data.Website}" target="_blank">${data.Website}</a>` : 'No website available'}<br>
                    <strong>Hours:</strong>
                    <ul>${data.Hours ? data.Hours.map(hour => `<li>${hour}</li>`).join('') : 'No open hours information available'}
                    </ul>
                    ${directionsLink}<br>
                    <a href="#" class="report-link" data-name="${data.Name}" data-toggle="modal" data-target="#reportModal">Report Bad Information</a>
                </p>
            </div>
        </div>
    `;
}

// Add event listener for report links
$(document).on('click', '.report-link', function() {
    const locationName = $(this).data('name');
    $('#location').val(locationName);
});