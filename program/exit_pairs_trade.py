from constants import CLOSE_AT_ZSCORE_CROSS
from public import get_recent_price_data
from private import check_if_any_open_positions, open_market_position 
from utils import format_number
from bot_agent import Bot
from cointegration import calculate_zscore
import pandas as pd
import numpy as np 
import pprint as pprint
import json

#function here to close a pairs trade based on certain z-score criteria
#need to check that the data on dydx platform is the same as the data in the json file 

def exit_trade(client):


    new_positions_output = []

    try:
        open_positions_json = open("bot_agents.json")
        open_positions_dict = json.load(open_positions_json)
    except Exception as e:
        return "Complete"

    # if there is no open positions
    if len(open_positions_dict) == 0:
        return "Complete"
    
    #get data from dydx for the client's open positions

    platform_data = client.private.get_positions(status="OPEN")
    platform_data_positions = platform_data.data["positions"]
    markets_live = []

    for m in platform_data_positions:
        # user positions that are open on dydx
        markets_live.append(m["market"])

    # loop through each open position in the dictionary and perform checks 
    for position in open_positions_dict:
        #close trigger
        close_pair_position = False
        coin_1 = position['coin_1']
        coin_2 = position['coin_2']
        coin_1_size = position['coin_1_size']
        coin_2_size = position['coin_2_size']
        coin_1_side = position['coin_1_side']
        coin_2_side = position['coin_2_side']
        

        # get coin info from dydx platform to perform check
        order_1 = client.private.get_order_by_id(position['coin_1_orderId'])
        order_1_size = order_1.data['order']['size']
        order_1_side = order_1.data['order']['side']
        order_1_coin = order_1.data['order']['market']

        order_2 = client.private.get_order_by_id(position['coin_2_orderId'])
        order_2_size = order_2.data['order']['size']
        order_2_side = order_2.data['order']['side']
        order_2_coin = order_2.data['order']['market']


        coin_1_check = coin_1 == order_1_coin and coin_1_side == order_1_side and coin_1_size == order_1_size
        coin_2_check = coin_2 == order_2_coin and coin_2_side == order_2_side and coin_2_size == order_2_size
        check_live = coin_1 in markets_live and coin_2 in markets_live 

        if not coin_1_check or not coin_2_check or not check_live :
            print(f"Warning --  data for open position for {coin_1} and {coin_2} is not the same")
            continue
    
        #use this to construct current z_score
        coin_1_price_series = get_recent_price_data(client, coin_1)
        coin_2_price_series = get_recent_price_data(client, coin_2)
        markets = client.public.get_markets().data

        if CLOSE_AT_ZSCORE_CROSS:
            hedge_ratio = position['hedge_ratio']
            old_z_score = position['z_score']
            if len(coin_1_price_series) > 0 and len(coin_1_price_series) == len(coin_2_price_series):
                spread = coin_1_price_series - (coin_2_price_series * hedge_ratio)
                z_score = calculate_zscore(spread).values.tolist()[-1]
                #logic to close trade
                z_score_check = abs(z_score) >= abs(old_z_score)
                z_score_final_check = (z_score > 0 and old_z_score < 0) or (z_score < 0 and old_z_score > 0)
                if z_score_final_check and z_score_check:
                    close_pair_position = True

            
            if close_pair_position:
                coin_1_new_side = "BUY" if coin_1_side == "SELL" else "SELL"
                coin_2_new_side = "BUY" if coin_2_side == "SELL" else "SELL"
                latest_coin_1_price = float(coin_1_price_series[-1])
                latest_coin_2_price = float(coin_2_price_series[-1])
                coin1_base_price = (latest_coin_1_price) * 1.05 if coin_1_new_side == "BUY" else (latest_coin_1_price) * 0.95
                coin2_base_price = (latest_coin_2_price) * 1.05 if coin_2_new_side == "BUY" else (latest_coin_2_price) * 0.95
                coin1_tick_size = markets["markets"][coin_1]["tickSize"]
                coin2_tick_size = markets["markets"][coin_2]["tickSize"]
                coin1_base_price = format_number(coin1_base_price, coin1_tick_size)
                coin2_base_price = format_number(coin2_base_price, coin2_tick_size)

                try:
                    coin_1_close_order = open_market_position(
                        client,
                        coin_1,
                        coin_1_new_side,
                        coin_1_size,
                        coin1_base_price,
                        True

                    )    
                    print(f"Closing order with {coin_1}")    
                    coin_2_close_order = open_market_position(
                        client,
                        coin_2,
                        coin_2_new_side,
                        coin_2_size,
                        coin2_base_price,
                        True

                    )
                    print(f"Closing order with {coin_2}")    
                except Exception as e:
                    print(f"Failed to exit position with {coin_1} and {coin_2}")
                    new_positions_output.append(position)
            # if need not close the position
            else:
                new_positions_output.append(position)

    print(new_positions_output)
    if len(new_positions_output) > 0:
        with open("bot_agents.json", "w") as f:
            json.dump(new_positions_output, f)





