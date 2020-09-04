import glob
import csv
import pandas as pd

def dataframe2dict(filename):
    """
    change the dataframe into a very large dictionary of dictionaries
    { timestamps: {
            companies: {
                    open:
                    close:
                        ...
                        }
            }
    }
    """
    df = pd.read_csv(filename)
    val_cols = ['open', 'close', 'high', 'low', 'volume']
    times = pd.unique(df['timestamp'])
    y = dict()
    for time in times:
        x = df.loc[df['timestamp']==time].to_dict()
        inds = list(x['company'].keys())
        tmp = dict()
        for i in inds:
            tmp[x['company'][i]] = {col: x[col][i] for col in val_cols}
        y[time] = tmp
    return y

def load_csv(filename):
    with open(filename, "r") as fh:
        reader = csv.DictReader(fh, delimiter=",")
        data = list(filter(lambda x: x['Open'] != 'None', reader))
    return data

def csv2dict(directory, filter_str="*.csv", big_dict={}):
    """
    Data is scraped into csv on a per company basis.
    We want to organized the data with time as the keys
    Once we download all the new stock data. add it to the old stock dictionary

    Args:
        directory: str
            location of csv files to be processed
        filter_str: str
            string to filter out csv files that need to be added
        big_dict: dictionary
            original dictionary to be updated
    Returns:
        big_dict: dictionary with new time values updated

    """
    # Get all filter to parse
    intra_files = glob.glob(f"{directory}/"+filter_str)
    # Tmp dictionary to hold all the data loaded
    # since there is overlap in the time frames of new data
    tmp_dict = {}

    for filename in intra_files:
        # Files are saved in format "STOCK_date.csv"
        # remove anyleading directory info and get the stock name
        stock = filename.split("/")[-1].split("_")[0]
        data = load_csv(filename)
        for item in data:
            # Use both the date and time are separate keys
            date_time = item['Time']
            date = date_time.split(" ")[0].strip()
            time = date_time.split(" ")[1].strip()

            company_dict = { stock: {
                                "open":   item['Open'],
                                "close":  item['Close'],
                                "high":   item['High'],
                                "low":    item['Low'],
                                "volume": item['Volume'],
                                 }
                           }
            # Handle cases where this is first instance of date time keys
            if tmp_dict.get(date):
                if tmp_dict[date].get(time):
                    tmp_dict[date][time].update(company_dict)
                else:
                    tmp_dict[date].update({time: {}})
                    tmp_dict[date][time].update(company_dict)
            else:
                tmp_dict[date] = {}
                if tmp_dict[date].get(time):
                    tmp_dict[date][time].update(company_dict)
                else:
                    tmp_dict[date].update({time: {}})
                    tmp_dict[date][time].update(company_dict)

    # Only update new keys into larger dictionary
    for k in tmp_dict.keys():
        if k not in big_dict.keys()
            big_dict[k] = tmp_dict[k]

    return big_dict


if __name__ == "__main__":
    pass
