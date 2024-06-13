let trusteeData = [];
let foodPantryData = [];
let countyData = [];
let map;
let markers = [];

$(document).ready(function() {
    const countySelect = $('#countySelect');

    fetch('utilities/data/counties_bounding_boxes.json')
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
        displayResults(selectedCounty);
        updateMap(selectedCounty);
    });

    fetch('utilities/data/indiana_township_trustees.json')
        .then(response => response.json())
        .then(data => {
            trusteeData = data;
        })
        .catch(error => console.error('Error loading trustee data:', error));

    fetch('utilities/data/indiana_food_pantries.json')
        .then(response => response.json())
        .then(data => {
            foodPantryData = data;
        })
        .catch(error => console.error('Error loading food pantry data:', error));

    initializeMap();
});

function initializeMap() {
    map = L.map('map').setView([40.2672, -86.1349], 7); // Centered on Indiana
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

function updateMap(county) {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    const countyInfo = countyData.find(c => c.name === county);
    if (countyInfo) {
        const bbox = countyInfo.bbox;
        const bounds = [[bbox.southwest.lat, bbox.southwest.lng], [bbox.northeast.lat, bbox.northeast.lng]];
        map.fitBounds(bounds);
    }

    const trustees = trusteeData.filter(item => item.County === county);
    const foodPantries = foodPantryData.filter(item => item.County === county);

    trustees.forEach(trustee => {
        const marker = L.marker([trustee.Latitude, trustee.Longitude]).addTo(map);
        marker.bindPopup(createPopupContent(trustee, 'Trustee'));
        markers.push(marker);
    });

    foodPantries.forEach(foodPantry => {
        const marker = L.marker([foodPantry.Latitude, foodPantry.Longitude]).addTo(map);
        marker.bindPopup(createPopupContent(foodPantry, 'Food Pantry'));
        markers.push(marker);
    });

    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}

function createPopupContent(data, type) {
    return `
        <strong>${data.Name} (${type})</strong><br>
        <strong>Address:</strong> ${data.Address}<br>
        <strong>Phone:</strong> <a href="tel:${data.Phone}">${data.Phone}</a><br>
        <strong>Website:</strong> ${data.Website && data.Website !== "N/A" ? `<a href="${data.Website}" target="_blank">${data.Website}</a>` : 'No website available'}<br>
        <strong>Hours:</strong><br>
        <ul>${data.Hours ? data.Hours.map(hour => `<li>${hour}</li>`).join('') : 'No open hours information available'}</ul>
        <a href="#" class="report-link" data-name="${data.Name}" data-toggle="modal" data-target="#reportModal">Report Bad Information</a>
    `;
}

function displayResults(county) {
    const resultsDiv = $('#results');
    resultsDiv.empty();

    const trustees = trusteeData.filter(item => item.County === county);
    const foodPantries = foodPantryData.filter(item => item.County === county);

    if (trustees.length === 0 && foodPantries.length === 0) {
        resultsDiv.append('<p>No data available for this county.</p>');
        return;
    }

    trustees.forEach(trustee => {
        resultsDiv.append(createCard(trustee, 'Trustee'));
    });

    foodPantries.forEach(foodPantry => {
        resultsDiv.append(createCard(foodPantry, 'Food Pantry'));
    });

    // Add event listener for report links
    $('.report-link').on('click', function() {
        const locationName = $(this).data('name');
        $('#location').val(locationName);
    });
}

function createCard(data, type) {
    return `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">${data.Name} (${type})</h5>
                <p class="card-text">
                    <strong>Address:</strong> ${data.Address}<br>
                    <strong>Phone:</strong> <a href="tel:${data.Phone}">${data.Phone}</a><br>
                    <strong>Website:</strong> ${data.Website && data.Website !== "N/A" ? `<a href="${data.Website}" target="_blank">${data.Website}</a>` : 'No website available'}<br>
                    <strong>Hours:</strong>
                    <ul>
                    ${data.Hours ? data.Hours.map(hour => `<li>${hour}</li>`).join('') : 'No open hours information available'}
                    </ul>
                    <a href="#" class="report-link" data-name="${data.Name}" data-toggle="modal" data-target="#reportModal">Report Bad Information</a>
                </p>
            </div>
        </div>
    `;
}
