from datetime import datetime, timedelta
#function here to format the number to the right format

def format_number(current,accepted):
    current_string = f"{current}"
    accepted_string = f"{accepted}" 

    #if there is decimals
    if "." in accepted_string:
        #eg 54.12 --> [54, 12], thus [1]
        num_of_accepted_decimals = len(accepted_string.split(".")[1])
        current_string = f"{current:.{num_of_accepted_decimals}f}"
        
        return current_string
    else:
        return f"{int(current)}"

# iso times are needed for the dydx api to get candles between an iso time period
#iso standard is year-month-date / hour-minute-second

def format_iso(timestamp):
    return timestamp.replace(microsecond=0).isoformat()

def get_ISO_times():
    #about 16 days worth 
    current = datetime.now()
    prev_1 = (current - timedelta(hours = 100))
    prev_2 = (prev_1 - timedelta(hours = 100))
    prev_3 = (prev_2 - timedelta(hours = 100))
    prev_4 = (prev_3 - timedelta(hours = 100))


    times = {
        "range_1": {
            "from":format_iso(prev_1),
            "to": format_iso(current)
        },
        "range_2": {
            "from":format_iso(prev_2),
            "to": format_iso(prev_1)
        },
        "range_3": {
            "from":format_iso(prev_3),
            "to": format_iso(prev_2)
        },
        "range_4": {
            "from":format_iso(prev_4),
            "to": format_iso(prev_3)
        },
    }
    return times