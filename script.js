const indianaCounties = [
    "Adams", "Allen", "Bartholomew", "Benton", "Blackford", "Boone", "Brown",
    "Carroll", "Cass", "Clark", "Clay", "Clinton", "Crawford", "Daviess",
    "Dearborn", "Decatur", "DeKalb", "Delaware", "Dubois", "Elkhart",
    "Fayette", "Floyd", "Fountain", "Franklin", "Fulton", "Gibson",
    "Grant", "Greene", "Hamilton", "Hancock", "Harrison", "Hendricks",
    "Henry", "Howard", "Huntington", "Jackson", "Jasper", "Jay", "Jefferson",
    "Jennings", "Johnson", "Knox", "Kosciusko", "LaGrange", "Lake",
    "LaPorte", "Lawrence", "Madison", "Marion", "Marshall", "Martin",
    "Miami", "Monroe", "Montgomery", "Morgan", "Newton", "Noble",
    "Ohio", "Orange", "Owen", "Parke", "Perry", "Pike", "Porter",
    "Posey", "Pulaski", "Putnam", "Randolph", "Ripley", "Rush", "St. Joseph",
    "Scott", "Shelby", "Spencer", "Starke", "Steuben", "Sullivan",
    "Switzerland", "Tippecanoe", "Tipton", "Union", "Vanderburgh",
    "Vermillion", "Vigo", "Wabash", "Warren", "Warrick", "Washington",
    "Wayne", "Wells", "White", "Whitley"
];

let trusteeData = [];
let foodPantryData = [];

$(document).ready(function() {
    const countySelect = $('#countySelect');
    indianaCounties.forEach(county => {
        countySelect.append(`<option value="${county}">${county}</option>`);
    });

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
                    <strong>Phone:</strong> ${data.Phone}<br>
                    <strong>Website:</strong> ${data.Website}<br>
                    <strong>Hours:</strong>
                    <ul>
                        ${data.Hours.map(hour => `<li>${hour}</li>`).join('')}
                    </ul>
                </p>
            </div>
        </div>
    `;
}
