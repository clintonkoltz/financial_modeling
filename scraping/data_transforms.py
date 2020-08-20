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

def csv2dict(directory):
    intra_files = glob.glob(f"{directory}/*.csv")
    big_dict = {}
    for filename in intra_files:
        ticker = filename.split("/")[-1].split("_")[0]
        data = load_csv(filename)
        for item in data:
            date_time = item['Time']
            # TODO
            # This probably needs to be changed for how the directory is input  
            date = date_time.split(" ")[0].strip()
            time = date_time.split(" ")[1].strip()
            company_dict = { ticker: {
                                "open":   item['Open'],
                                "close":  item['Close'],
                                "high":   item['High'],
                                "low":    item['Low'],
                                "volume": item['Volume'],
                                 }
                           }
            if big_dict.get(date):
                if big_dict[date].get(time):
                    big_dict[date][time].update(company_dict)
                else:
                    big_dict[date].update({time: {}})
                    big_dict[date][time].update(company_dict)
            else:
                big_dict[date] = {}
                if big_dict[date].get(time):
                    big_dict[date][time].update(company_dict)
                else:
                    big_dict[date].update({time: {}})
                    big_dict[date][time].update(company_dict)

    return big_dict


if __name__ == "__main__":
    pass
