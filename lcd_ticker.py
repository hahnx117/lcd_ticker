# https://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# https://finnhub.io/docs/api

import time
from datetime import datetime
import finnhub
import requests
from bs4 import BeautifulSoup
import I2C_LCD_driver

def get_vix_price():
    """Use BeautifulSoup to get the CBOE Volatility Index."""

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0'}

    ticker = "^VIX"
    url = f"https://finance.yahoo.com/quote/{ticker}"

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    price = soup.select_one(f'fin-streamer[data-field="regularMarketPrice"][data-symbol="{ticker}"]')
    percent_change = soup.select_one(f'fin-streamer[data-field="regularMarketChangePercent"][data-symbol="{ticker}"]')

    return {"vix_value": float(price['data-value']),"vix_percent_change": float(percent_change['data-value'])}



TICKERS = ["DJT", "TSLA", "RDDT"]
FINNHUB_API_KEY = ""
NOAA_URL = "https://api.weather.gov/gridpoints/MPX/108,71/forecast"
BTC_URL = "https://blockchain.info/ticker"
BASEURL = "https://pro-api.coinmarketcap.com"
COINMARKETCAP_API_KEY = ""
BASIC_CREDITS = 10000

parameters = {
    'symbol': 'TRUMP,MELANIA',
    'convert': 'USD'
}

headers = {
  'Accepts': 'application/json',
  'X-CMC_PRO_API_KEY': f'{COINMARKETCAP_API_KEY}',
}

baseline_time = datetime.now()
current_month = baseline_time.month

credits_used = 7
first_pull = False

if baseline_time.hour >= 5 and baseline_time.hour <= 18:
    at_desk = True
else:
    at_desk = False

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)
mylcd = I2C_LCD_driver.lcd()

while True:
    ## First get the stock tickers we're interested in
    quote_string = []

    for i in TICKERS:
        quote = finnhub_client.quote(i)

        # c: current price, d: change, dp: percent change, h: high of the day, l: low of the day, o: open price, pc: previous close
        quote_string .append(f"{i}: {quote['c']:.2f} ({quote['dp']:.2f})")

        quote = None

    ## Get the ^VIX information
#    vix_dict = get_vix_price()

    ## Get $TRUMP and $MELANIA info
    timepoint = datetime.now()
    if ((timepoint - baseline_time).seconds / 60 >= 5 or not first_pull) and at_desk:
        crypto_response = requests.get(f"{BASEURL}/v2/cryptocurrency/quotes/latest", headers=headers, params=parameters)
        crypto_response.raise_for_status()

        credits_used += crypto_response.json()['status']['credit_count']
        baseline_time = timepoint
        if timepoint.month != current_month:
            credits_used = 0
            current_month = timepoint.month
        first_pull = True

    ## Get weather information
    noaa_response = requests.get(NOAA_URL)
    current_forecast = noaa_response.json()['properties']['periods'][0]

    ## Lastly little ol bitcoin
    btc_response = requests.get(BTC_URL)
    btc_price = btc_response.json()['USD']['last']

    ## Now let's display this on the LCD

    ## Clear the lcd

    mylcd.lcd_clear()

    ## Display stock info
    mylcd.lcd_display_string(quote_string[0], 1)
    mylcd.lcd_display_string(quote_string[1], 2)
    mylcd.lcd_display_string(quote_string[2], 3)
    time.sleep(5)

    mylcd.lcd_clear()

    ## Display VIX
#    mylcd.lcd_display_string(f"^VIX: {vix_dict['vix_value']:.2f} ({vix_dict['vix_percent_change']:.2f})", 2, 1)
#    time.sleep(5)

#    mylcd.lcd_clear()

    ## Display BTC
    mylcd.lcd_display_string(f"BTC: ${btc_price:,}", 2, 2)
    time.sleep(5)

    mylcd.lcd_clear()

    ##Display $TRUMP and $MELANIA
    mylcd.lcd_display_string("$TRUMP:", 1)
    mylcd.lcd_display_string(f"  {crypto_response.json()['data']['TRUMP'][0]['quote']['USD']['price']:.2f} ({crypto_response.json()['data']['TRUMP'][0]['quote']['USD']['percent_change_24h']:.2f}%)", 2)
    mylcd.lcd_display_string("$MELANIA:", 3)
    mylcd.lcd_display_string(f"  {crypto_response.json()['data']['MELANIA'][0]['quote']['USD']['price']:.2f} ({crypto_response.json()['data']['MELANIA'][0]['quote']['USD']['percent_change_24h']:.2f}%)", 4)
    time.sleep(8)

    mylcd.lcd_clear()

    ## Display credits remaining for Crypto API
    mylcd.lcd_display_string("Last pull:", 1)
    mylcd.lcd_display_string(f"    {baseline_time.strftime('%a %b %d')}", 2)
    mylcd.lcd_display_string(f"    {baseline_time.strftime('%H:%M %P')}", 3)
    mylcd.lcd_display_string(f"Creds rem: {(BASIC_CREDITS - credits_used)}", 4)
    time.sleep(5)

    mylcd.lcd_clear()

    ## Display weather
    mylcd.lcd_display_string(f"Temp: {current_forecast['temperature']}{current_forecast['temperatureUnit']}", 1)
    mylcd.lcd_display_string(f"Wind: {current_forecast['windSpeed']}", 2)
    mylcd.lcd_display_string(f"Wind dir: {current_forecast['windDirection']}", 3)
    mylcd.lcd_display_string(f"Precip: {current_forecast['probabilityOfPrecipitation']['value']}%", 4)
    time.sleep(10)

