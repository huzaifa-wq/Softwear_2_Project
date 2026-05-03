let playerId = null;
let currentContracts = []; // ✅ global storage for contracts

async function startGame() {
  let playerName = document.getElementById('playerName').value;
  if (!playerName) {
    alert("Please enter your name before starting the game!");
    return;
  }

  let res = await fetch('http://127.0.0.1:5000/start_game', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: playerName})
  });

  let data = await res.json();
  playerId = data.player_id;

  // ✅ Greeting message
  document.getElementById('greeting').innerHTML =
    "Welcome aboard Captain " + data.player_name + " !";
  document.getElementById('greeting').classList.add("show");

  getStatus();
}

// Get Player Status
async function getStatus() {
  let res = await fetch(`http://127.0.0.1:5000/status/${playerId}`);
  let data = await res.json();

  document.getElementById('status').innerHTML =
    `Money: ${data.money} | Fuel: ${data.fuel} | Turns left: ${data.turns_left}`;

  // Update progress bars
  updateBar("fuelBar", data.fuel, 2000);       // MAX_FUEL = 2000
  updateBar("moneyBar", data.money, 3000);     // TARGET_MONEY = 3000
  updateBar("turnsBar", data.turns_left, 15);  // TOTAL_TURNS = 15


  function updateBar(barId, value, max) {
  let percent = (value / max) * 100;
  document.getElementById(barId).style.width = percent + "%";
}

  //  Update fuel price in refuel box
  let fuelPriceElement = document.getElementById("fuel-price");
  if (fuelPriceElement && data.fuel_price !== undefined) {
    fuelPriceElement.innerText = `Fuel price: ${data.fuel_price.toFixed(2)} €/unit`;
  }

  //  Update current airport marker
  updateMap(data);

  //  Fetch contracts once (same data for list + map)
  getContracts();

}


// Get Contracts
async function getContracts() {
  let res = await fetch(`http://127.0.0.1:5000/contracts/${playerId}`);
  currentContracts = await res.json(); //  store contracts globally

  //  Update contracts list in UI
  let html = "<h3>Available Contracts</h3>";
  currentContracts.forEach((c, i) => {
    html += `<button onclick="deliver(${i})">
              ${c.destination_name} (${c.distance} km, Reward: ${c.reward}€, Fuel: ${c.fuel_needed})
             </button><br>`;
  });
  document.getElementById('contracts').innerHTML = html;

  //  Update map markers with same contracts
  updateContractsOnMap(currentContracts);
}

// Deliver Cargo
async function deliver(index) {
  let chosen = currentContracts[index]; //  use stored contracts

  chosen.reward = parseInt(chosen.reward);
  chosen.fuel_needed = parseInt(chosen.fuel_needed);

  let res2 = await fetch(`http://127.0.0.1:5000/deliver/${playerId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(chosen)
  });

  let data = await res2.json();

  //  Show result in styled box instead of alert
  let deliveryBox = document.getElementById("delivery-result");
  if (deliveryBox) {
    deliveryBox.innerText = data.message;
  }

  //  Optional: if win condition triggered, show modal too
  if (data.message.includes("Congratulations")) {
    showWinModal(data.message);
  }
  getStatus(); //  refresh status after delivery

}

//  Refuel via frontend box (not prompt)

async function doRefuel() {
  let amount = document.getElementById("refuel-amount").value;

  if (!amount || isNaN(amount) || amount <= 0) {
    alert("Please enter a valid fuel amount.");
    return;
  }

  let res = await fetch(`http://127.0.0.1:5000/refuel/${playerId}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({fuel_amount: parseInt(amount)})
  });

  let result = await res.json();

  //  Show result in styled box (same look as refuel box)

  let refuelBox = document.getElementById("refuel-result");
  if (refuelBox) {
    refuelBox.innerText = result.message;
  }

  getStatus(); // refresh progress bars
}

// Initialize map
let map = L.map('map').setView([60.1699, 24.9384], 4); // Default center (Helsinki)

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Markers storage
let currentMarker = null;
let contractMarkers = [];

//  Update current airport marker only
function updateMap(status) {
  if (currentMarker) {
    map.removeLayer(currentMarker);
  }

  const redIcon = L.icon({
    iconUrl: 'https://maps.gstatic.com/mapfiles/ms2/micons/red-dot.png',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });

  if (status.latitude && status.longitude) {
    currentMarker = L.marker([status.latitude, status.longitude], { icon: redIcon })
      .addTo(map)
      .bindPopup(`Current Airport: ${status.current_airport || status.location}`)
      .openPopup();

    map.setView([status.latitude, status.longitude], 5);
  }
}

//  Update contracts markers (always green)

function updateContractsOnMap(contracts) {
  contractMarkers.forEach(m => map.removeLayer(m));
  contractMarkers = [];

  const greenIcon = L.icon({
    iconUrl: 'https://maps.gstatic.com/mapfiles/ms2/micons/green-dot.png',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });

  contracts.forEach(c => {
    if (c.latitude && c.longitude) {
      let marker = L.marker([c.latitude, c.longitude], {icon: greenIcon})
          .addTo(map)
          .bindPopup(`${c.destination_name} (${c.distance} km, Reward: ${c.reward}€, Fuel: ${c.fuel_needed})`);
      contractMarkers.push(marker);
    }
  });
}

