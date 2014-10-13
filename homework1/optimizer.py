# QSTK Imports
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import QSTK.qstkutil.DataAccess as da

import datetime as dt
import numpy as np
import pandas as pd
from math import sqrt

# recursive combination generator - generates integer combinations
# remaining: number of elements
# amount: the sum of all elements
# returns: a list containing all combinations of integers that sum to given amount
def gen_comb(remaining, amount):
    if remaining == 1:
        yield [amount]
    else:
        for i in range(amount+1):
            for tail in gen_comb(remaining-1,amount-i):
                yield [i] + tail

# for a given set of normalized daily returns and allocation, simulate the performance
# na_normalized_price: numpy array of normalized daily prices by stock
# ls_alloc: list of percentage allocations for each stock
# returns: volatility, avg daily return, sharpe ratio, cumulative returns
def simulate(na_normalized_price, ls_alloc):

    # Calculate the daily returns of the prices.
    na_port_daily_returns = np.sum(na_normalized_price * ls_alloc, axis=1)
    tsu.returnize0(na_port_daily_returns)

    std_dev = na_port_daily_returns.std()
    daily_ret = na_port_daily_returns.mean()
    sharpe = sqrt(252) * daily_ret / std_dev
    cum_ret = 1 + na_port_daily_returns.sum()

    return std_dev, daily_ret, sharpe, cum_ret

# for a given set of equities and a date range, find the allocation
# that will optimize for the best Sharpe ratio
def main():

    # List of symbols and date range
    # ideally we'd pass these in as args - change as needed
    ls_symbols = ['AAPL', 'GOOG', 'IBM', 'MSFT']
    dt_start = dt.datetime(2011, 1, 1)
    dt_end = dt.datetime(2011, 12, 31)

    # We need closing prices so the timestamp should be hours=16.
    dt_timeofday = dt.timedelta(hours=16)

    # Get a list of trading days between the start and the end.
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt_timeofday)

    # Creating an object of the dataaccess class with Yahoo as the source.
    c_dataobj = da.DataAccess('Yahoo')

    # Keys to be read from the data, it is good to read everything in one go.
    ls_keys = ['open', 'high', 'low', 'close', 'volume', 'actual_close']

    # Reading the data, now d_data is a dictionary with the keys above.
    ldf_data = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))

    # get close prices, fill empty values, and put in a numpy array
    df_close_price = d_data['close'].copy()
    df_close_price = df_close_price.fillna(method='ffill')
    df_close_price = df_close_price.fillna(method='bfill')
    na_price = df_close_price.values

    # Normalizing the prices to start at 1 and see relative returns
    na_normalized_price = na_price / na_price[0, :]

    # find all valid portfolio allocations in increments of .1 (10%)
    ls_valid_alloc = (np.array(list(gen_comb(len(ls_symbols), 10)), dtype=float) / 10).tolist()

    best_sharpe = 0.0
    best_alloc = np.zeros((1, len(ls_symbols)))
    best_stddev = 0.0
    best_daily_ret = 0.0
    best_cum_ret = 0.0
    for ls_alloc in ls_valid_alloc:
        # calculate stats for this allocation
        std_dev, daily_ret, sharpe, cum_ret = simulate(na_normalized_price, ls_alloc)
        if sharpe > best_sharpe:
            best_alloc = ls_alloc
            best_stddev = std_dev
            best_daily_ret = daily_ret
            best_sharpe = sharpe
            best_cum_ret = cum_ret

    print "Best Allocation : ", best_alloc
    print "Best Sharpe     : ", best_sharpe
    print "Best Std Dev    : ", best_stddev
    print "Best Cum Returns: ", best_cum_ret
    print "Best Avg Daily  : ", best_daily_ret

if __name__ == '__main__':
    main()