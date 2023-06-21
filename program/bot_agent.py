from private import open_market_position, get_position_status, open_market_position_2
from datetime import datetime, timedelta
from pprint import pprint
import time
from utils import format_number
from messaging_bot import send_messages
class Bot:
    def __init__(self,
    client,
    coin_1,
    coin_2,
    coin_1_side,
    coin_1_size,
    coin_1_prize,
    coin_2_side,
    coin_2_size,
    coin_2_prize,
    accept_failsafe_base_price,
    z_score,
    hedge_ratio,
    half_life
    ):
        self.client = client
        self.coin_1 = coin_1
        self.coin_2 = coin_2
        self.coin_1_side = coin_1_side
        self.coin_1_size = coin_1_size
        self.coin_1_prize = coin_1_prize
        self.coin_2_side = coin_2_side
        self.coin_2_size = coin_2_size
        self.coin_2_prize = coin_2_prize
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.hedge_ratio = hedge_ratio
        self.half_life = half_life

        #output variable
        self.order_dict = {
            "coin_1":coin_1,
            "coin_2":coin_2,
            "hedge_ratio":hedge_ratio,
            "z_score":z_score,
            "half_life":half_life,
            "coin_1_orderId":"",
            "coin_2_orderId":"",
            "coin_1_side": coin_1_side,
            "coin_2_side":coin_2_side,
            "coin_1_size":coin_1_size,
            "coin_2_size":coin_2_size,
            "coin_1_orderTime":"",
            "coin_2_orderTime":"",
            #based on pair_status
            "pair_status":"",
            "comments":"",
            "date_closed":"",
            "coin_1_realized_pnl":"",
            "coin_2_realized_pnl":"",

        }
    
    #check order status by id --> update [air status based on order_status]

    def check_order_status_by_id(self, order_id):
        status = get_position_status(self.client, order_id)
        if order_id == "":
            return "failed"
        if status == 'CANCELED':
            print(f"{self.coin_1} and {self.coin_2} order cancelled")
            self.order_dict["pair_status"] = 'FAILED'
            return "failed"
        
        
        if status != 'FAILED':
            time.sleep(15)
            status = get_position_status(self.client, order_id)
            if status == 'CANCELED':
                print(f"{self.coin_1} and {self.coin_2} order cancelled")
                self.order_dict["pair_status"] = 'FAILED'
                return "failed"

            #if the order is still not filled
            if status != 'FILLED':
                print(f"{self.coin_1} and {self.coin_2} order error")
                self.order_dict["pair_status"] = 'ERROR'
                return "failed"

        return "live"

    #function to open trades


    def open_trades(self):
        print(f"Opening a {self.coin_1_side} trade with {self.coin_1} ")

        try:
            order_coin1 = open_market_position(
            self.client,
            self.coin_1,
            self.coin_1_side,
            self.coin_1_size,
            self.coin_1_prize,
            False
            )
            self.order_dict["coin_1_orderId"] = order_coin1["order"]["id"]
            self.order_dict["coin_1_orderTime"] = datetime.now().isoformat()
        except Exception as e:
            self.order_dict["pair_status"] = 'FAILED'    
            self.order_dict["comments"] = "Failed to open trade : {e}"
            print(f"Failed to open trade with {self.coin_1} : {e}")
            return self.order_dict
            
        #check successful place of first order
        order_status = self.check_order_status_by_id(self.order_dict["coin_1_orderId"])
        if order_status != 'live':
            self.order_dict["pair_status"] = 'FAILED'    
            self.order_dict["comments"] = f"Failed to open trade with {self.coin_1}"
            print(f"Failed to open trade with {self.coin_1}")
            return self.order_dict
           
        
        #proceed with the second trade
        print(f"Opening a {self.coin_2_side} trade with {self.coin_2} ")
        try:
            order_coin2 = open_market_position(
            self.client,
            self.coin_2,
            self.coin_2_side,
            self.coin_2_size,
            self.coin_2_prize,
            False
            )
            self.order_dict["coin_2_orderId"] = order_coin2["order"]["id"]
            self.order_dict["coin_2_orderTime"] = datetime.now().isoformat()
            
        except Exception as e:
            self.order_dict["pair_status"] = 'FAILED'    
            self.order_dict["comments"] = f"Failed to open trade {self.coin_2} : {e}"
            print(f"Failed to open trade with {self.coin_2} : {e}")
            print(self.order_dict)
            
        
        order_status_coin2 = self.check_order_status_by_id(self.order_dict["coin_2_orderId"])
        print(order_status_coin2)
        if order_status_coin2 != 'live':
            self.order_dict["pair_status"] = 'FAILED'    
            self.order_dict["comments"] = f"Failed to open trade with {self.coin_2}"
            print(f"Failed to open trade with {self.coin_2}. Attempting to close order with {self.coin_1} now...")
            
            try:
                #since order_2 is not successful need to cancel the first order
                #this order here need not be a FOK
                #use a GTT type order to ensure that the order has a high chance of being filled
                worst_case_price = float(self.coin_1_prize) * 1.7 if self.coin_2_side == "BUY" else float(self.coin_1_prize) * 0.3
                markets = self.client.public.get_markets().data
                tick_size = markets["markets"][self.coin_1]["tickSize"]
                worst_case_price = format_number(worst_case_price, tick_size)
                cancel_coin1_order = open_market_position(
                    self.client,
                    self.coin_1,
                    self.coin_2_side,
                    self.coin_1_size,
                    worst_case_price,
                    True
                )
                #waiting to be filled
                time.sleep(10)
                #check if the cancelling order1 was successful
                cancel_coin1_order_status = get_position_status(self.client, cancel_coin1_order["order"]["id"])
                print(cancel_coin1_order_status)
                #if cannot cancel this order, need to send a message to the operator and need to kill the program
                if cancel_coin1_order_status != 'FILLED':
                    print("Kill program")
                    send_messages("INTERVENE.. UNABLE TO CLOSE ORDER FOR THE FIRST TRADED PAIR")
                    exit(1)
                else:
                    self.order_dict["pair_status"] = 'CLOSED SUCCESSFULLY'    
                    self.order_dict["comments"] = f"Failed to open trade with {self.coin_2} but closed open order with {self.coin_1} successfully"
                    return self.order_dict
            except Exception as e:
                self.order_dict["pair_status"] = 'FAILED'    
                self.order_dict["comments"] = f"Failed to close trade {self.coin_1}: {e}"
                print(f"Failed to close trade with {self.coin_1} : {e}")
                send_messages("INTERVENE.. UNABLE TO CLOSE ORDER FOR THE FIRST TRADED PAIR")
                exit(1)
                
        
        #order2 success:
        else:
         
            self.order_dict["pair_status"] = "LIVE"
            self.order_dict["comments"] = "success pair trading"
            return self.order_dict
