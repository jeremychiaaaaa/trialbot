from datetime import datetime, timedelta
from utils import format_number
import time
import json

def check_order_status(client, order_id):
  order = client.private.get_order_by_id(order_id)
  if order.data:
    if "order" in order.data.keys():
      return order.data["order"]["status"]
  return "FAILED"
#function to get the status of a client's position
def get_position_status(client, order_id):
    order = client.private.get_order_by_id(order_id)
    if order.data:
        if "order" in order.data.keys():
            return order.data["order"]["status"]
    return "FAILED"


#function to check if there are any current open orders for an existing market
def check_if_any_open_positions(client, market):
    all_positions = client.private.get_positions(market=market, status="OPEN")
    print((all_positions.data['positions']))
    if len(all_positions.data['positions']) > 0:
        return True
    else:
        return False

#function to open a positions
def open_market_position(client, market, side, size, price, reduce_only):
    account_response = client.private.get_account()
    position_id = account_response.data["account"]["positionId"]


    #place order
    placed_order = client.private.create_order(
    position_id=position_id, # required for creating the order signature
    market=market,
    side=side,
    order_type="MARKET",
    post_only=False,
    size=size,
    # this price here refers to the worst acceptable price
    #the worst acceptable price for long order is higher than the current price
    price=price,
    limit_fee='0.015',
    expiration_epoch_seconds=time.time() + 65,
    time_in_force="FOK",
    reduce_only = reduce_only
    )

    return placed_order.data


#close all opened orders ( ie buy / sell a short / long order   )
def close_orders(client):
    client.private.cancel_all_orders()

    markets = client.public.get_markets().data
    #all open positions currently
    positions =  client.private.get_positions(status="OPEN")
    all_positions = positions.data["positions"]

    close_orders = []
    #if theres open positions, loop through each one and create a corresponding closing market order base on the "side" whether is buy or sell. make sure the price set matches the tick_size using the helper function to calculate
    #setting reduce_only = True makes sure to close the current market order
    if len(all_positions) > 0:
        for position in all_positions:
            
            market = position["market"]
            side = "BUY"
            if position["side"] == "LONG":
                side = "SELL"

            price = float(position["entryPrice"])
            worst_case_price = price * 1.7 if side == "BUY" else price * 0.3
            tick_size = markets["markets"][market]["tickSize"]
            # need a function to calculate the right acceptable price based on the accepted price and the tick_size for different coins (more specifically on the number of decimals)
            worst_case_price = format_number(worst_case_price, tick_size)
            #use the place market order function in this case to close the order
            order = open_market_position(
                client,
                market,
                side,
                #size is the sumOpen within the position object
                position["sumOpen"],
                worst_case_price,
                True
            )
            close_orders.append(order)

    bot_res = []
    with open("bot_agents.json", "w") as f:
        #converts into a json file, second param is the json file to receive the object
        
        json.dump(bot_res, f)
    return close_orders