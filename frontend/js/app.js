/* 
=============================================
  SmartRescue EMS - Frontend Logic
=============================================
*/

const API_BASE_URL = 'https://daa-smartrescue.onrender.com';

// ═══════════════════════════════════════════════════════════════
//  1. LEAFLET MAP INITIALIZATION
// ═══════════════════════════════════════════════════════════════

// Initialize the map centered near PCMC / Pune
const map = L.map('map', {
    zoomControl: false // We'll customize zoom controls later if needed
}).setView([18.6298, 73.7997], 13);

// Using a dark-themed tile layer to match our premium aesthetic
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// Example static markers for visual feel (matching backend locations roughly)
const pcmcLocations = [
    { name: "Base", coords: [18.6298, 73.7997] },
    { name: "YCM Hospital", coords: [18.6256, 73.8123] },
    { name: "Aditya Birla Hospital", coords: [18.6201, 73.7554] },
    { name: "PCCOE", coords: [18.6517, 73.7614] },
    { name: "Nigdi", coords: [18.6483, 73.7719] }
];

// Add markers
pcmcLocations.forEach(loc => {
    // Basic Leaflet marker, you can customize this extensively
    L.circleMarker(loc.coords, {
        color: '#00F0FF',
        radius: 8,
        fillOpacity: 0.8,
        weight: 2
    }).addTo(map).bindPopup(`<b>${loc.name}</b>`);
});

// Remove initialization placeholder text
const mapPlaceholder = document.querySelector('.map-placeholder');
if (mapPlaceholder) {
    mapPlaceholder.style.display = 'none';
}


// ═══════════════════════════════════════════════════════════════
//  2. INVENTORY PANEL: 0/1 KNAPSACK INTEGRATION
// ═══════════════════════════════════════════════════════════════

const btnCalcLoadout = document.getElementById('btn-calc-loadout');
const capacitySlider = document.getElementById('capacity-slider');
const inventoryTableBody = document.querySelector('#inventory-table tbody');
const loadoutSummary = document.getElementById('loadout-summary');

btnCalcLoadout.addEventListener('click', async () => {
    // 1. Get capacity from slider
    const capacity = parseInt(capacitySlider.value, 10);

    // 2. Initial UI loading state
    inventoryTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Calculating DP Matrix...</td></tr>';
    loadoutSummary.classList.add('hidden');
    btnCalcLoadout.innerHTML = 'Computing...';
    btnCalcLoadout.disabled = true;

    try {
        // 3. Make POST request to Flask API
        const response = await fetch(`${API_BASE_URL}/api/knapsack`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ capacity: capacity })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // 4. Update Table
            inventoryTableBody.innerHTML = '';

            if (data.items_selected.length === 0) {
                inventoryTableBody.innerHTML = '<tr><td colspan="3" class="empty-state">Capacity too low. No items selected.</td></tr>';
            } else {
                data.items_selected.forEach(item => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td style="color: #FFF; font-weight: 500;">${item.name}</td>
                        <td style="color: #94A3B8;">${item.weight} kg</td>
                        <td style="color: #05FF00;">+${item.value}</td>
                    `;
                    inventoryTableBody.appendChild(row);
                });
            }

            // 5. Update Summary Card
            loadoutSummary.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94A3B8; font-size: 0.85rem;">Total Payload Weight:</span>
                    <strong style="color: #FFF;">${data.total_weight} / ${data.capacity} kg</strong>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 0.5rem;">
                    <span style="color: #94A3B8; font-size: 0.85rem;">Maximized Priority Score:</span>
                    <strong style="color: #00F0FF; font-size: 1.1rem; text-shadow: 0 0 10px rgba(0,240,255,0.4);">${data.max_value}</strong>
                </div>
            `;
            loadoutSummary.classList.remove('hidden');
            loadoutSummary.style.padding = '1rem';
            loadoutSummary.style.background = 'rgba(0, 240, 255, 0.05)';
            loadoutSummary.style.border = '1px solid rgba(0, 240, 255, 0.2)';
            loadoutSummary.style.borderRadius = '8px';
            loadoutSummary.style.marginBottom = '1rem';

        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error("Error calculating loadout:", error);
        inventoryTableBody.innerHTML = `<tr><td colspan="3" style="text-align:center; color: #FF2A6D;">Error: Could not reach backend server. Is Flask running?</td></tr>`;
    } finally {
        // Reset button
        btnCalcLoadout.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Calculate Optimal Loadout
        `;
        btnCalcLoadout.disabled = false;
    }
});


// ═══════════════════════════════════════════════════════════════
//  3. TRANSPORT ROUTING PANEL: TSP Branch & Bound
// ═══════════════════════════════════════════════════════════════

const btnCalcRoute = document.getElementById('btn-calc-route');
const routeOutput = document.getElementById('route-output');

btnCalcRoute.addEventListener('click', async () => {

    // 1. Initial UI Loading State
    routeOutput.innerHTML = '<span>Branching and Bounding...</span>';
    routeOutput.classList.remove('empty');
    btnCalcRoute.innerHTML = 'Computing...';
    btnCalcRoute.disabled = true;

    try {
        // 2. Fetch TSP result from backend
        const response = await fetch(`${API_BASE_URL}/api/tsp`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.status === 'success') {

            if (data.route_names.length === 0) {
                routeOutput.innerHTML = `<span style="color:#FF2A6D;">No valid route found. Grpah may be disconnected.</span>`;
                return;
            }

            // 3. Format the route visually
            const routeHtml = data.route_names.map((city, index) => {
                const isStartEnd = index === 0 || index === data.route_names.length - 1;
                return `
                    <div style="display:inline-flex; align-items:center; gap:0.5rem;">
                        <span style="color: ${isStartEnd ? '#05FF00' : '#FFF'}; font-weight: ${isStartEnd ? '700' : '500'};">
                            ${city}
                        </span>
                        ${index < data.route_names.length - 1 ? `<span style="color: var(--secondary); font-size: 0.8rem; margin: 0 0.2rem;">→</span>` : ''}
                    </div>
                `;
            }).join('');

            // 4. Render output
            routeOutput.innerHTML = `
                <div style="display: flex; flex-direction: column; width: 100%; gap: 1rem;">
                    <div style="display: flex; justify-content: center; flex-wrap: wrap; text-align: center; line-height: 1.8;">
                        ${routeHtml}
                    </div>
                    <div style="background: rgba(255, 42, 109, 0.1); border: 1px solid rgba(255, 42, 109, 0.3); padding: 0.75rem; border-radius: 8px; text-align: center;">
                        <span style="color: #94A3B8; font-size: 0.85rem; margin-right: 0.5rem;">Total Estimated Time:</span>
                        <strong style="color: #FF2A6D; font-size: 1.1rem;">${data.total_time} mins</strong>
                    </div>
                </div>
            `;

        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error("Error calculating TSP route:", error);
        routeOutput.innerHTML = `<span style="color:#FF2A6D; text-align:center;">Error: Could not connect to API.</span>`;
    } finally {
        // Reset button
        btnCalcRoute.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>
            Calculate Optimal Supply Route
        `;
        btnCalcRoute.disabled = false;
    }
});
