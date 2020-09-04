from datetime import datetime

def convert_date(date_str, time=False):
    """ Date conversion with handling the
    two formats used. with/without time
    Also handle the blank case for some inital
    conditions needed
    """
    if date_str == "":
        return ""
    if (time):
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    else:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    return date

def split_datetime_str(date_str):
    tmp = date_str.split(" ")
    assert len(tmp) == 2, f"Date time in wrong format {date_str}"
    date = tmp[0]
    time = tmp[1]
    return date, time


