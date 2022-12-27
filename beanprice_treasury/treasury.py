import decimal
from typing import Optional, List
from datetime import datetime, timedelta

import requests
from dateutil.tz import tz

try:
    from beanprice import source
except:
    from beancount.prices import source


class TreasuryDirectError(ValueError):
    "Error from loading urls at Treasury Direct"


def _get_price(ticker: str, fetch_time: datetime) -> Optional[source.SourcePrice]:
    url = "https://treasurydirect.gov/GA-FI/FedInvest/securityPriceDetail"
    payload = {
        'priceDateDay': fetch_time.day,
        'priceDateMonth': fetch_time.month,
        'priceDateYear': fetch_time.year,
        'fileType': 'csv',
        'csv': 'CSV+FORMAT',
    }
    response = requests.post(url, params=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        result_lines = response.text.split('\n')
    except TreasuryDirectError as error:
        raise TreasuryDirectError("%s (ticker: %s)" % (error, ticker)) from error

    # emtpy string is returned if requested day is a holiday
    if len(result_lines) == 1 and result_lines[0] == '':
        return None

    try:
        result = next(l for l in result_lines if l.startswith(ticker + ','))

        # CUSIP	SECURITY,TYPE,RATE,MATURITY DATE,CALL DATE,BUY,SELL,END OF DAY
        # 91282CFS5,MARKET BASED FRN,0.04539212635,10/31/2024,,99.855912,99.833481,99.835275
        price_value = result.split(',')[7]

        if float(price_value) == 0: # this is probably an incomplete day
            return None

        price = decimal.Decimal(price_value)
    except StopIteration:
        raise TreasuryDirectError('Ticker {} is not found'.format(ticker))
    except decimal.InvalidOperation:
        raise TreasuryDirectError('Ticker {} value is not valid: {}'.format(ticker, price_value))

    timezone = tz.gettz('America/New_York')
    return source.SourcePrice(price, fetch_time.astimezone(timezone), 'USD')


def _get_latest_price(ticker: str, fetch_time: datetime) -> Optional[source.SourcePrice]:
    """ get latest price as of fetch_time """
    fetch_time = datetime.now()

    while (datetime.now() - fetch_time).days < 6:
        if fetch_time.weekday() >= 5:  # skip weekends
            fetch_time = fetch_time - timedelta(days=1)
            continue

        ret = _get_price(ticker, fetch_time)

        if ret is None:  # it might be an incomplete day or a federal holiday
            fetch_time = fetch_time - timedelta(days=1)
        else:
            return ret


class Source(source.Source):
    def get_latest_price(self, ticker: str) -> Optional[source.SourcePrice]:
        """See contract in beanprice.source.Source."""

        return _get_latest_price(ticker, datetime.now())


    def get_historical_price(self, ticker: str,
                             time: datetime) -> Optional[source.SourcePrice]:
        """See contract in beanprice.source.Source."""

        return _get_latest_price(ticker, time)
