// static/symbol_lookup.js - CORRECTED

document.addEventListener('DOMContentLoaded', function() {
    // --- Get references to the HTML elements ---
    // Make sure the IDs ('symbol', 'token', 'exchange', 'symbol-list')
    // match the actual IDs in your HTML template where this script is used.
    const symbolInput = document.getElementById('symbol');
    const tokenInput = document.getElementById('token');
    const exchangeInput = document.getElementById('exchange');
    const symbolList = document.getElementById('symbol-list'); // This should be a <datalist> element

    // --- Check if elements were found ---
    // Important for debugging if IDs don't match HTML
    if (!symbolInput || !tokenInput || !exchangeInput || !symbolList) {
        console.error("Symbol lookup script: One or more required elements (symbol, token, exchange, symbol-list) not found. Check HTML IDs.");
        return; // Stop execution if elements are missing
    }

    console.log("Symbol lookup script loaded and elements found."); // Confirmation

    // Load stocks.json
    fetch('/static/stocks.json') // Assuming stocks.json is in the static folder
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const stockDict = {};
            // Populate the dictionary AND the initial datalist
            data.forEach(entry => {
                // Use uppercase symbol as the key for consistent lookup later
                const upperSymbol = entry.symbol.toUpperCase();
                stockDict[upperSymbol] = { token: entry.token, exchange: entry.exchange, originalSymbol: entry.symbol }; // Store original case if needed

                // Add option to the datalist
                const option = document.createElement('option');
                option.value = entry.symbol; // Show original case in dropdown
                symbolList.appendChild(option);
            });
            console.log(`Loaded ${Object.keys(stockDict).length} stocks into dictionary.`);

            // Autocomplete Filtering on Input
            symbolInput.addEventListener('input', function() {
                const typedValue = symbolInput.value.toUpperCase();
                const matchingSymbols = Object.values(stockDict) // Iterate over values to get original symbols
                                          .map(details => details.originalSymbol) // Get the original case symbol
                                          .filter(s => s.toUpperCase().includes(typedValue)); // Filter based on uppercase comparison

                symbolList.innerHTML = ''; // Clear previous dynamic options
                matchingSymbols.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol; // Use original case symbol for the value
                    symbolList.appendChild(option);
                });
            });

            // Auto-fill Token and Exchange on Change (when a selection is made)
            symbolInput.addEventListener('change', function() {
                const selectedSymbolKey = symbolInput.value.toUpperCase(); // Use uppercase for lookup
                if (stockDict[selectedSymbolKey]) {
                    tokenInput.value = stockDict[selectedSymbolKey].token;
                    exchangeInput.value = stockDict[selectedSymbolKey].exchange;
                    // Optional: Normalize the input field display to the original case
                    // symbolInput.value = stockDict[selectedSymbolKey].originalSymbol;
                    console.log(`Filled data for: ${selectedSymbolKey}`);
                } else {
                    // Clear fields if the input doesn't match a known symbol after selection
                    // Don't clear if the user is just typing (handled by 'input' event)
                    if (symbolInput.value !== '') { // Avoid clearing if field is simply emptied
                       console.log(`No exact match found for: ${selectedSymbolKey}. Clearing token/exchange.`);
                       tokenInput.value = '';
                       exchangeInput.value = '';
                    }
                }
            });

            console.log("Symbol lookup event listeners attached.");

        })
        .catch(error => {
             console.error('Error loading or processing stocks.json in symbol_lookup.js:', error);
        });

}); // End of DOMContentLoaded
