let trusteeData = [];
let foodPantryData = [];

$(document).ready(function() {
    const countySelect = $('#countySelect');

    fetch('utilities/data/counties.json')
        .then(response => response.json())
        .then(data => {
            data.forEach(county => {
                countySelect.append(`<option value="${county}">${county}</option>`);
            });
        })
        .catch(error => console.error('Error loading counties:', error));

    countySelect.change(function() {
        const selectedCounty = $(this).val();
        displayResults(selectedCounty);
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
});

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
                </p>
            </div>
        </div>
    `;
}
