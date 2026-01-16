let countyData = [];
let map;
let markers = [];

$(document).ready(function() {
    const countySelect = $('#countySelect');
    const filterSelect = $('#filterSelect');
    const addressForm = $('#addressForm');
    const zipForm = $('#zipForm');
    const addressInput = $('#addressInput');
    const zipInput = $('#zipInput');
    const resultsDiv = $('#results');
    const findNearestBtn = $('#findNearestBtn');
    const errorMessageDiv = $('#error-message');

    function showError(message) {
        errorMessageDiv.text(message).fadeIn();
        setTimeout(() => errorMessageDiv.fadeOut(), 5000);
    }

    function clearError() {
        errorMessageDiv.hide();
    }

    async function loadCountyData() {
        try {
            const response = await fetch('static/utilities/data/counties_bounding_boxes.json');
            if (!response.ok) throw new Error('Failed to load county data');
            const data = await response.json();
            countyData = data;

            countySelect.append(`<option value="" selected>Select a county</option>`);
            data.forEach(county => {
                countySelect.append(`<option value="${county.name}">${county.name}</option>`);
            });
        } catch (error) {
            console.error('Error loading counties:', error);
            showError('Failed to load county data. Please refresh the page.');
        }
    }

    loadCountyData();

    findNearestBtn.click(async function () {
        clearError();
        if (!navigator.geolocation) {
            showError("Geolocation is not supported by this browser.");
            return;
        }

        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject);
            });

            const { latitude, longitude } = position.coords;

            const response = await fetch(`/reverse-geocode?lat=${latitude}&lon=${longitude}`);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to find resources');
            }

            const data = await response.json();
            resultsDiv.empty();

            if (data.trustee) {
                const trustee = data.trustee;

                if (trustee.Latitude && trustee.Longitude) {
                    const marker = L.marker([trustee.Latitude, trustee.Longitude], { icon: trusteeIcon }).addTo(map);
                    marker.bindPopup(createPopupContent(trustee, 'Trustee'));
                    markers.push(marker);
                    map.setView([trustee.Latitude, trustee.Longitude], 12);
                    marker.openPopup();
                }

                resultsDiv.append(createCard(trustee, 'Trustee'));
            }

            if (data.food_pantries && data.food_pantries.length > 0) {
                data.food_pantries.forEach(pantry => {
                    if (pantry.Latitude && pantry.Longitude) {
                        const marker = L.marker([pantry.Latitude, pantry.Longitude], { icon: foodPantryIcon }).addTo(map);
                        marker.bindPopup(createPopupContent(pantry, 'Food Pantry'));
                        markers.push(marker);
                    }

                    resultsDiv.append(createCard(pantry, 'Food Pantry'));
                });
            }

            if (!data.trustee && (!data.food_pantries || data.food_pantries.length === 0)) {
                showError("No trustee or food pantry information found for your location.");
            }
        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'Failed to get your location or find resources.');
        }
    });

    countySelect.change(function() {
        const selectedCounty = $(this).val();
        if (selectedCounty) {
            clearError();
            const selectedFilter = filterSelect.val();
            loadCountyResources(selectedCounty, selectedFilter);
        }
    });

    filterSelect.change(function() {
        const selectedCounty = countySelect.val();
        if (selectedCounty) {
            clearError();
            const selectedFilter = $(this).val();
            loadCountyResources(selectedCounty, selectedFilter);
        }
    });

    function handleGeocodeResult(data) {
        clearError();
        if (data.error) {
            showError(data.error);
            return;
        }

        if (data.trustee) {
            const trustee = data.trustee;

            markers.forEach(marker => map.removeLayer(marker));
            markers = [];

            if (trustee.Latitude && trustee.Longitude) {
                const marker = L.marker([trustee.Latitude, trustee.Longitude], { icon: trusteeIcon }).addTo(map);
                marker.bindPopup(createPopupContent(trustee, 'Trustee'));
                markers.push(marker);

                map.setView([trustee.Latitude, trustee.Longitude], 12);
                marker.openPopup();
            } else {
                showError("No office information for your trustee has been found. However, other data may be available below.");
            }

            resultsDiv.empty();
            resultsDiv.append(createCard(trustee, 'Trustee'));

        } else if (data.county) {
            showError(`No immediate trustee found for your address in ${data.county}. Showing other results in that area.`);
            countySelect.val(data.county).change();
        } else {
            showError('Address or zip not found or invalid');
        }
    }

    zipForm.submit(async function(event) {
        event.preventDefault();
        clearError();
        const zip = zipInput.val();
        if (!zip) return;

        try {
            const response = await fetch(`/geocode?zip=${encodeURIComponent(zip)}`);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to geocode zip code');
            }
            const data = await response.json();
            handleGeocodeResult(data);
        } catch (error) {
            console.error('Error geocoding zip:', error);
            showError(error.message || 'Failed to find location for the provided zip code.');
        }
    });

    addressForm.submit(async function(event) {
        event.preventDefault();
        clearError();
        const address = addressInput.val();
        if (!address) return;

        try {
            const response = await fetch(`/geocode?address=${encodeURIComponent(address)}`);
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to geocode address');
            }
            const data = await response.json();
            handleGeocodeResult(data);
        } catch (error) {
            console.error('Error geocoding address:', error);
            showError(error.message || 'Failed to find location for the provided address.');
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

async function loadCountyResources(county, filter) {
    try {
        const response = await fetch(`/county-resources?county=${encodeURIComponent(county)}&filter=${filter}`);
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to load county resources');
        }
        const data = await response.json();
        displayResults(data, filter);
        updateMap(data, county, filter);
    } catch (error) {
        console.error('Error loading county resources:', error);
        showError(error.message || 'Failed to load resources for this county.');
    }
}

function updateMap(data, county, filter) {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];

    const countyInfo = countyData.find(c => c.name === county);
    if (countyInfo) {
        const bbox = countyInfo.bbox;
        const bounds = [[bbox.southwest.lat, bbox.southwest.lng], [bbox.northeast.lat, bbox.northeast.lng]];
        map.fitBounds(bounds);
    }

    if (data.trustees) {
        data.trustees.forEach(trustee => {
            if (trustee.Latitude && trustee.Longitude) {
                const marker = L.marker([trustee.Latitude, trustee.Longitude], { icon: trusteeIcon }).addTo(map);
                marker.bindPopup(createPopupContent(trustee, 'Trustee'));
                markers.push(marker);
            }
        });
    }

    if (data.food_pantries) {
        data.food_pantries.forEach(foodPantry => {
            if (foodPantry.Latitude && foodPantry.Longitude) {
                const marker = L.marker([foodPantry.Latitude, foodPantry.Longitude], { icon: foodPantryIcon }).addTo(map);
                marker.bindPopup(createPopupContent(foodPantry, 'Food Pantry'));
                markers.push(marker);
            }
        });
    }

    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds());
    }
}

function createResourceDetails(data, type) {
    const directionsLink = data.Address ?
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(data.Address)}" target="_blank">Get Directions</a>` :
        `<a href="https://www.google.com/maps/dir/?api=1&destination=${data.Latitude},${data.Longitude}" target="_blank">Get Directions</a>`;

    return `
        <strong>Address:</strong> ${data.Address}<br>
        <strong>Phone:</strong> <a href="tel:${data.Phone}">${data.Phone}</a><br>
        <strong>Website:</strong> ${data.Website && data.Website !== "N/A" ? `<a href="${data.Website}" target="_blank">${data.Website}</a>` : 'No website available'}<br>
        <strong>Hours:</strong>
        <ul>${data.Hours && data.Hours.length > 0 ? data.Hours.map(hour => `<li>${hour}</li>`).join('') : 'No open hours information available'}</ul>
        ${directionsLink}<br>
        <a href="#" class="report-link" data-name="${data.Name}" data-toggle="modal" data-target="#reportModal">Report Issues</a>
    `;
}

function createPopupContent(data, type) {
    return `
        <strong><em>Please note that not all locations are offices, please call before traveling to the location.</em></strong><br>
        <strong>${data.Name} (${type})</strong><br>
        ${createResourceDetails(data, type)}
    `;
}

function displayResults(data, filter) {
    const resultsDiv = $('#results');
    resultsDiv.empty();

    if (data.trustees) {
        data.trustees.forEach(trustee => {
            resultsDiv.append(createCard(trustee, 'Trustee'));
        });
    }

    if (data.food_pantries) {
        data.food_pantries.forEach(foodPantry => {
            resultsDiv.append(createCard(foodPantry, 'Food Pantry'));
        });
    }

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
                    ${createResourceDetails(data, type)}
                </p>
            </div>
        </div>
    `;
}

$(document).on('click', '.report-link', function() {
    const locationName = $(this).data('name');
    $('#location').val(locationName);
});
