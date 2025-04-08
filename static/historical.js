document.addEventListener('DOMContentLoaded', function() {
    const symbolInput = document.getElementById('symbol');
    const tokenInput = document.getElementById('token');
    const exchangeInput = document.getElementById('exchange');
    const intervalSelect = document.getElementById('interval');
    const fromDateInput = document.getElementById('from_date');
    const fromHourInput = document.getElementById('from_hour');
    const fromMinuteInput = document.getElementById('from_minute');
    const toDateInput = document.getElementById('to_date');
    const toHourInput = document.getElementById('to_hour');
    const toMinuteInput = document.getElementById('to_minute');
    const symbolList = document.getElementById('symbol-list');

    // Load stocks.json
    fetch('/static/stocks.json') // Assuming stocks.json is in the static folder
        .then(response => response.json())
        .then(data => {
            const stockDict = {};
            data.forEach(entry => {
                stockDict[entry.symbol] = { token: entry.token, exchange: entry.exchange };
                const option = document.createElement('option');
                option.value = entry.symbol;
                symbolList.appendChild(option);
            });

            // Autocomplete and Auto-fill
            symbolInput.addEventListener('input', function() {
                const typedValue = symbolInput.value.toUpperCase();
                const matchingSymbols = Object.keys(stockDict).filter(s => s.includes(typedValue));
                symbolList.innerHTML = '';
                matchingSymbols.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol;
                    symbolList.appendChild(option);
                });
            });

            symbolInput.addEventListener('change', function() {
                const selectedSymbol = symbolInput.value.toUpperCase();
                if (stockDict[selectedSymbol]) {
                    tokenInput.value = stockDict[selectedSymbol].token;
                    exchangeInput.value = stockDict[selectedSymbol].exchange;
                } else {
                    tokenInput.value = '';
                    exchangeInput.value = '';
                }
            });
        });

    // Set default values for date and time
    const today = new Date();
    const todayFormatted = today.toISOString().split('T')[0];
    fromDateInput.value = todayFormatted;
    toDateInput.value = todayFormatted;

    // Update time defaults based on interval
    function updateTimeDefaults() {
        const interval = intervalSelect.value.toUpperCase();
        if (interval === "ONE_DAY") {
            fromHourInput.value = "00";
            fromMinuteInput.value = "00";
            toHourInput.value = "23";
            toMinuteInput.value = "59";
        } else {
            fromHourInput.value = "09";
            fromMinuteInput.value = "00";
            toHourInput.value = "15";
            toMinuteInput.value = "30";
        }
    }

    // Bind the update function to the interval select change
    intervalSelect.addEventListener('change', updateTimeDefaults);

    // Set defaults for initial state based on ONE_DAY
    updateTimeDefaults();
});
