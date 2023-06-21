from dydx3.constants import API_HOST_GOERLI
from decouple import config

#The file here will be the constants used during the creating of the bot

#only need to do this once in a while (eg once a day --> control flow for fetching historical data)
FIND_COINTEGRATED = False

#run once every week
BACKTESTING = False

PLACE_TRADES = True
# abort all positions is a constant to facilitate testing during development

ABORT_ALL_POSITIONS = True

#when to exit positions
MANAGE_EXITS = True
#time period
RESOLUTION = "1DAY"

#window for each calculation of the rolling average that will be used during z-score
WINDOW = 21
#setting exit zscore threshold to be 1.0 for backtesting
ZSC0RE_EXIT_THRESHOLD = 1.0

#threshold for opening a trade
MAX_HALF_LIFE = 24
ZSCORE_THRESH = 1.5
USD_PER_TRADE = 100
#min amount in account before the bot will execute any trade
USD_MIN_COLLATERAL = 100
CLOSE_AT_ZSCORE_CROSS = True

TOKEN_FACTOR_10 = ["XLM-USD","DOGE-USD","TRX-USD"]
ETHEREUM_ADDRESS = "0x64e907C2De215d91FF299444BF6dF76Bd611Ee72"

ETH_PRIVATE_KEY = config("ETH_PRIVATE_KEY")
STARK_PRIVATE_KEY = config("STARK_PRIVATE_KEY")
DYDX_API_KEY = config("DYDX_API_KEY")
DYDX_API_SECRET = config("DYDX_API_SECRET")
DYDX_API_PASSPHRASE = config("DYDX_API_PASSPHRASE")

HOST = API_HOST_GOERLI

HTTP_PROVIDER = "https://eth-goerli.g.alchemy.com/v2/WIVt4hDtPNlP5sfjPh-rEk8zy_DFCVvW"

