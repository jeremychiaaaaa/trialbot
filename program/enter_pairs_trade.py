from constants import ZSCORE_THRESH, USD_MIN_COLLATERAL, USD_PER_TRADE, TOKEN_FACTOR_10
from public import get_recent_price_data
from private import check_if_any_open_positions
from utils import format_number
from bot_agent import Bot
from cointegration import calculate_zscore
import pandas as pd
import numpy as np 
import pprint as pprint
import json


def place_trades(client):
    #from the cointegratred data previoisly calculatd
    # took the top 30
    df = pd.read_csv("filtered_cointegrated_pairs.csv")
    
    #get all markets
    markets = client.public.get_markets().data

    bot_res = [] 
    try:
        open_positions_json = open("bot_agents.json")
        open_positions_dict = json.load(open_positions_json)
        for p in open_positions_dict:
            bot_res.append(p)
    except Exception as e:
        bot_res = [] 
    #finding z_score triggers
    for index, row in df.iterrows():
        coin_1 = row["series_1"]
        coin_2 = row["series_2"]
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]
        
        #calculate z_score
        recent_data_coin1 = get_recent_price_data(client, coin_1)
        recent_data_coin2 = get_recent_price_data(client, coin_2)

        if len(recent_data_coin1) > 0 and len(recent_data_coin1) == len(recent_data_coin2):
            spread = recent_data_coin1 - (recent_data_coin2 * hedge_ratio)
            #returns a series of recent z_score based on the spread 
            z_score = calculate_zscore(spread).values.tolist()[-1]
            # check if z_score is within this threshold
            if abs(z_score) >= ZSCORE_THRESH:
                print(coin_1)
                #make sure dont open the same type of pair-pair trade

                is_coin1_open = check_if_any_open_positions(client, coin_1)
                is_coin2_open = check_if_any_open_positions(client, coin_2)
                print(is_coin1_open)
                if not is_coin1_open and not is_coin2_open:
                    coin_1_side = "BUY" if z_score < 0 else "SELL"
                    coin_2_side = "BUY" if z_score > 0 else "SELL"

                    
                    #setting up prices
                    coin1_base_price = float(recent_data_coin1[-1]) * 1.01 if z_score < 0 else float(recent_data_coin1[-1]) * 0.99
                    
                    coin2_base_price = float(recent_data_coin2[-1]) * 1.01 if z_score > 0 else float(recent_data_coin2[-1]) * 0.99
                   
                    failsafe_base_price = float(recent_data_coin1[-1]) * 0.05 if z_score < 0 else float(recent_data_coin1[-1]) * 1.7
                    
                    # get tick sizes and then format base price for each coin to fit the decimal places of the tick size respectively
                    #print(markets)
                    coin1_tick_size = markets["markets"][coin_1]["tickSize"]
                    coin2_tick_size = markets["markets"][coin_2]["tickSize"]
                  
                    coin1_base_price = format_number(coin1_base_price, coin1_tick_size)
                    coin2_base_price = format_number(coin2_base_price, coin2_tick_size)
                    failsafe_base_price = format_number(failsafe_base_price, coin1_tick_size)
                    
                  

                    if float(coin1_base_price) < 0.1:
                        print("here")
                        coin1_size = round((1 / float(coin1_base_price) * USD_PER_TRADE) / 10) * 10
                    else:
                        coin1_size = 1 / float(coin1_base_price) * USD_PER_TRADE
 
                    if float(coin2_base_price) < 0.1:
                        coin2_size = round((1 / float(coin2_base_price) * USD_PER_TRADE) / 10) * 10
                    else:
                        coin2_size = 1 / float(coin2_base_price) * USD_PER_TRADE


                    


                    
                    coin1_step_size = markets["markets"][coin_1]["stepSize"]
                    coin2_step_size = markets["markets"][coin_2]["stepSize"]

                    #format sizes
                    coin1_size = format_number(coin1_size, coin1_step_size)
                    coin2_size = format_number(coin2_size, coin2_step_size)

                    #check if it is above minOrderSize stipulated by dydx 
                    min_order_size_coin1 = markets["markets"][coin_1]["minOrderSize"]
                    min_order_size_coin2 = markets["markets"][coin_2]["minOrderSize"]

                    check_coin1_size = (coin1_size) > min_order_size_coin1
                    check_coin2_size = (coin2_size) > min_order_size_coin2

                    #if checks pass, place trade
                    if check_coin1_size and check_coin2_size:
                        account = client.private.get_account()
                        amount_of_free_collateral = float(account.data["account"]["freeCollateral"])

                        #check if there is enough collateral
                        if amount_of_free_collateral <  USD_MIN_COLLATERAL:
                            break
                        
                        #create an instance of the bot agent
                        bot_agent = Bot(
                            client,
                            coin_1,
                            coin_2,
                            coin_1_side,
                            coin1_size,
                            coin1_base_price,
                            coin_2_side,
                            coin2_size,
                            coin2_base_price,
                            failsafe_base_price,
                            z_score,
                            hedge_ratio,
                            half_life
                        )

                        #open trades method
                        bot_open_dict = bot_agent.open_trades()
                 

                    # either try and see if there is no bug by deleting that particular pair from the csv
                    # add all dicts and then after that filter those only with pair status live before dumping into json file

                        if bot_open_dict["pair_status"] == "LIVE":
                            bot_res.append(bot_open_dict)
                            del(bot_open_dict)
                            print("LIVE")
                        else:
                            continue

    print(f"Success: {len(bot_res)} pairs now trading")
    print(bot_res)
    if len(bot_res) > 0:
        print('dumping')
        with open("bot_agents.json", "w") as f:
            #converts into a json file, second param is the json file to receive the object
            json.dump(bot_res, f)
    
