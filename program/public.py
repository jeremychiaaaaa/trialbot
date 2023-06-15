from utils import get_ISO_times
import pandas as pd
import numpy as np 
import time
from constants import RESOLUTION
from pprint import pprint


#function to get recent prices
def get_recent_price_data(client, market):
    prices = []
    candles = client.public.get_candles(
            market=market,
            resolution=RESOLUTION,
            limit=100
            )
    for candle in candles.data["candles"]:
        prices.append(candle["close"])
    
    prices.reverse()
    result = np.array(prices).astype(np.float)
    return result


#function to make the api call
def get_prices(client, market):
    prices = []
    ISO_times = get_ISO_times()
    for ranges in ISO_times.keys():
        curr = ISO_times[ranges]
        start_time = curr["from"]
        end_time = curr["to"]
        candles = client.public.get_candles(
            market=market,
            resolution=RESOLUTION,
            #from_iso=start_time,
            #to_iso=end_time,
            limit=100
        )
        for candle in candles.data["candles"]:
            prices.append({
            "datetime": candle["startedAt"],
            market: candle["close"]    
            })

    #this will arrange the data from old to new
    prices.reverse()
    return prices





# function to construct market prices data
def get_data(client):
    # need to get all the markets and check if thehy are available and tradeable and then store the historical prices in a pandas df using the get_prices function above
    tradeable_markets = []
    all_markets = client.public.get_markets()

    for market in all_markets.data["markets"].keys():
        market_info = all_markets.data["markets"][market]
        if market_info["status"] == "ONLINE" and market_info["type"] == "PERPETUAL":
            tradeable_markets.append(market)
    
    #initial dataframe
    client_data = get_prices(client, tradeable_markets[0])

    df = pd.DataFrame(client_data)
    df.set_index("datetime", inplace=True)


    #add other prices to the dataframe

    for markets in tradeable_markets[1:]:
        data = get_prices(client, markets)
        df_add = pd.DataFrame(data)
        df_add.set_index("datetime", inplace=True)
        df = pd.merge(df, df_add, how="outer", on="datetime", copy=False)
        del df_add

    # need to remove any columns (ie market) if there is any null value
    #any here returns a series corresponding to each column with a True or False value
    #this will filter out the columns with a True indicator meaning they have na values
    nans = df.columns[df.isna().any()].tolist()
    if len(nans) > 0:
        print("Removing NA columns")
        df.drop(columns=nans, inplace=True)
   
    return df