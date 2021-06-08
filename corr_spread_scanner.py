import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import time
import concurrent.futures
from tqdm import tqdm
import pathlib
import sqlite3
from itertools import chain
from symbols_lists import mt5_symbols, fin_symbols, spreads, trading_symbols
from ohlc_request import mt5_ohlc_request, _read_last_datetime
from create_db import ohlc_db, correlation_db
from tokens import mt5_login, mt5_pass, bot
from corr_value_scanner import _get_data, _normalize, cor_symbols


''' Unlike the value scanner which aggregates the correlated instruments, this
is going to focus exclusively on pairs of instruments (eg, AUDUSD + USDSGD). 
Spreads will likely be added in though at some point as an alternative to single 
instruments (AUDUSD + GOLD/OIL).  And instead of correlation being saved candle
by candle over a rolling window wherever it breaches the threshold, there won't be
a rolling window here. I'm looking for a high amount of correlation over a given 
period and then will use break downs in that correlation as trade alerts.

I'll need to track the average deviation in the correlation to set the alert
threshold.  Plus, I'll need to know the ADR of the instruments to filter out
the alerts where the actual price deviation (not corr. deviation) is too
small to trade.  Instruments which are too correlated, even with a corr break down,
won't offer enough room to trade.

I'll continue using M5 candles like in value_scanner.'''

# Correlation period (needs to be named like this for the imported functions)
HIST_CANDLES = 51840  # 160 days
MIN_CORR = 0.75

shift_periods = [0, 10, 50, 150, 300, 500, 750]

for key_symbol in trading_symbols:
    key_df = _get_data(key_symbol, key_symbol, _, HIST_CANDLES, hist_fill=True)

    final_df = pd.DataFrame(index=key_df.index)
    for cor_symbol in cor_symbols:
        cor_df = _get_data(key_symbol, cor_symbol, _, HIST_CANDLES, hist_fill=True)

        # Ensure matching df lengths (drop the overnight periods if there are any)
        temp_key_df = key_df[key_df.index.isin(cor_df.index)].copy() # to avoid warnings
        cor_df = cor_df[cor_df.index.isin(temp_key_df.index)].copy()

        temp_key_df = _normalize(temp_key_df, 'close')
        cor_df = _normalize(cor_df, 'close')

        # Iter various shifts to find highest cor and save the data to this dict
        shift_val = {
            'data': pd.DataFrame(dtype=np.float32),
            'best_sum': 0,
            'shift': 0
        }
        for shift in shift_periods:
            cor_values = temp_key_df.close.rolling(HIST_CANDLES).corr(cor_df.close.shift(shift))
            cor_values = cor_values.dropna()

            if cor_values.mean() > MIN_CORR or cor_values.mean() < -1 * MIN_CORR:
                # Update the shift dict
                if abs(cor_values).sum() > shift_val['best_sum']:
                    shift_val['best_sum'] = abs(cor_values).sum()
                    shift_val['data'] = round(cor_values, 3)
                    shift_val['shift'] = shift
        
        # If nothing is found jump to the next symbol
        if shift_val['data'].empty:
            continue
        
        # Now get the standard deviation 

def send_alert(msg, bot=bot):
    bot.send_message(chat_id=446051969, text=f'{msg}')

def _spreads_or_something(symbol1, symbol2, timeframe, period, threshold, less_than=True):
    ''' Some instruments are often highly correlated but at times can diverge.
    This often creates a trading opportunity that is easily missed without notifications.
    I'll use this function to alert me to pairs whose correlation is diverging
    https://prnt.sc/11atpjj '''

    key = _get_data(symbol1, timeframe=timeframe)
    cor = _get_data(symbol2, timeframe=timeframe)

    # Align
    key = key[key.index.isin(cor.index)].copy() # to avoid warnings
    cor = cor[cor.index.isin(key.index)]

    key = _normalize(key)
    cor = _normalize(cor)

    correlation = key.rolling(period).corr(cor)
    if less_than:
        if correlation.tail(1).values[0] <= threshold:
            send_alert(f'{symbol1}, {symbol2} correlation divergence.')
    else:        
        if correlation.tail(1).values[0] >= threshold:
            send_alert(f'{symbol1}, {symbol2} correlation divergence.')

if __name__ == '__main__':

    while True:
        _spreads_or_something('XAUUSD', 'XAGUSD', mt5_timeframes['M15'], 20, -0.2, )
        _spreads_or_something('AUDUSD', 'USDSGD', mt5_timeframes['M15'], 20, 0, less_than=False)
        time.sleep(15 * 60)
