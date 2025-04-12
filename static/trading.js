// static/trading.js - REVISED (Ensure IDs match HTML)

document.addEventListener('DOMContentLoaded', function() {
    console.log("Trading JS loaded."); // Confirm this script runs

    // --- Get references to HTML elements ---
    // Ensure these IDs EXACTLY match your trading.html
    const symbolInput = document.getElementById('symbol');
    const tokenInput = document.getElementById('token');         // Hidden input
    const exchangeInput = document.getElementById('exchange');   // Hidden input
    const symbolList = document.getElementById('symbol-list');   // Datalist element
    const orderTypeSelect = document.getElementById('order_type');
    const priceInput = document.getElementById('price');
    const triggerPriceInput = document.getElementById('trigger_price'); // Kept for UI toggling

    // --- Check if ALL required elements are found ---
    let elementsFound = true;
    if (!symbolInput) { console.error("Trading script: Missing element with ID 'symbol'"); elementsFound = false; }
    if (!tokenInput) { console.error("Trading script: Missing element with ID 'token'"); elementsFound = false; }
    if (!exchangeInput) { console.error("Trading script: Missing element with ID 'exchange'"); elementsFound = false; }
    if (!symbolList) { console.error("Trading script: Missing element with ID 'symbol-list'"); elementsFound = false; }
    if (!orderTypeSelect) { console.error("Trading script: Missing element with ID 'order_type'"); elementsFound = false; }
    if (!priceInput) { console.error("Trading script: Missing element with ID 'price'"); elementsFound = false; }
    if (!triggerPriceInput) { console.warn("Trading script: Missing element with ID 'trigger_price'. Trigger price toggling disabled."); } // Warn is ok

    if (!elementsFound) {
        console.error("Trading script: Halting execution due to missing critical elements.");
        return; // Stop if critical elements are missing
    }
    console.log("All critical trading elements found.");


    // --- Symbol Lookup Logic ---
    fetch('/static/stocks.json') // Ensure stocks.json is accessible at this path
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error loading stocks.json! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const stockDict = {};
            // Populate the dictionary AND the initial datalist
            data.forEach(entry => {
                // Use uppercase symbol as the key for consistent lookup
                const upperSymbol = entry.symbol.toUpperCase();
                // Store token, exchange, and original symbol case
                stockDict[upperSymbol] = { token: entry.token, exchange: entry.exchange, originalSymbol: entry.symbol };

                // Add option to the datalist using original case for display
                const option = document.createElement('option');
                option.value = entry.symbol;
                symbolList.appendChild(option);
            });
            console.log(`Loaded ${Object.keys(stockDict).length} stocks into dictionary.`);

            // --- Event Listener for Symbol Input (Autocomplete Filtering) ---
            symbolInput.addEventListener('input', function() {
                const typedValue = symbolInput.value.toUpperCase();
                // Filter based on original symbol containing typed value (case-insensitive)
                const matchingSymbols = Object.values(stockDict)
                                          .map(details => details.originalSymbol)
                                          .filter(s => s.toUpperCase().includes(typedValue));

                // Clear previous dynamic options (important for filtering)
                // Keep static options if any, or clear all if only dynamic
                symbolList.innerHTML = '';
                matchingSymbols.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol; // Use original case symbol for the value
                    symbolList.appendChild(option);
                });
                 // Also clear token/exchange while typing if no match is forming
                 const currentUpper = symbolInput.value.toUpperCase();
                 if (!stockDict[currentUpper]) {
                     // Avoid clearing if the field is empty
                     if (symbolInput.value !== '') {
                         tokenInput.value = '';
                         exchangeInput.value = '';
                     }
                 }
            });

            // --- Event Listener for Symbol Change (Selection Made) ---
            symbolInput.addEventListener('change', function() {
                const selectedSymbolKey = symbolInput.value.toUpperCase(); // Use uppercase for lookup
                if (stockDict[selectedSymbolKey]) {
                    // Populate hidden fields
                    tokenInput.value = stockDict[selectedSymbolKey].token;
                    exchangeInput.value = stockDict[selectedSymbolKey].exchange;
                    // Optional: Normalize the input field display to the original case found
                    // symbolInput.value = stockDict[selectedSymbolKey].originalSymbol;
                    console.log(`Filled Token/Exchange for: ${selectedSymbolKey} -> T:${tokenInput.value}, E:${exchangeInput.value}`);
                } else {
                    // Clear hidden fields if the final input doesn't match a known symbol
                    if (symbolInput.value !== '') { // Avoid clearing if field was simply emptied by user
                       console.log(`No exact match found for: ${selectedSymbolKey}. Clearing token/exchange.`);
                       tokenInput.value = '';
                       exchangeInput.value = '';
                    } else {
                        // Clear if field is empty
                        tokenInput.value = '';
                        exchangeInput.value = '';
                    }
                }
            });

            console.log("Symbol lookup event listeners attached.");

        })
        .catch(error => {
             console.error('Error loading or processing stocks.json in trading.js:', error);
             // Optionally display an error to the user on the page
        });
    // --- End Symbol Lookup Logic ---


    // --- Trading Form Specific Logic (Price/Trigger Price Toggling) ---
    // Check if triggerPriceInput exists before adding logic that uses it
    if (orderTypeSelect && priceInput) { // Trigger price is optional for this core logic
        function togglePriceFields() {
            const selectedOrderType = orderTypeSelect.value;
            console.log(`Order type changed to: ${selectedOrderType}`);

            // Price field logic
            const priceRequired = (selectedOrderType === 'LIMIT' || selectedOrderType === 'STOPLOSS_LIMIT');
            priceInput.disabled = !priceRequired;
            priceInput.required = priceRequired;
            if (!priceRequired && priceInput.value !== "0") { // Clear price if not required, unless it's already 0 (backend default)
                 // priceInput.value = ''; // Or keep value but make it non-required? Let's keep it simple: disable/enable + require/not require
            }
            console.log(`Price input disabled: ${priceInput.disabled}, required: ${priceInput.required}`);

            // Trigger Price field logic (only if element exists)
            if (triggerPriceInput) {
                const triggerRequired = (selectedOrderType === 'STOPLOSS_LIMIT' || selectedOrderType === 'STOPLOSS_MARKET');
                triggerPriceInput.disabled = !triggerRequired;
                triggerPriceInput.required = triggerRequired;
                if (!triggerRequired) {
                    // triggerPriceInput.value = ''; // Optional clear
                }
                console.log(`Trigger price input disabled: ${triggerPriceInput.disabled}, required: ${triggerPriceInput.required}`);
            } else {
                 console.log("Trigger price input not found, skipping toggle logic for it.");
            }
        }

        orderTypeSelect.addEventListener('change', togglePriceFields);
        togglePriceFields(); // Call once on load to set initial state
        console.log("Trading form price toggling listeners attached.");

    } // End Trading Form Logic

}); // End of DOMContentLoaded
