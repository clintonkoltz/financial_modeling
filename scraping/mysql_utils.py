import mysql.connector
import os
import csv
import glob

class DatabaseAdder:

    def __init__(self, file_dir, table_name):
        self.con = mysql.connector.connect(user="klinton", database="stocks", password="43MY39ka!")
        self.cur = self.con.cursor()
        self.files = glob.glob(os.path.join(file_dir,"*"))
        self.insert_new = (f"REPLACE INTO {table_name} (company, date, open, high, low, close, volume)"
                           "VALUES (%s, %s, %s, %s, %s, %s, %s)")

    def read_file(self, daily_file):
        with open(daily_file, "r") as fh:
            data = list(csv.DictReader(fh))
        return data

    def filename_to_ticker(self, filename):
        ticker = filename.split("/")[2].split("_")[0]
        return ticker

    def add_all_to_database(self):
        for day_file in self.files:
            ticker = self.filename_to_ticker(day_file)
            data = self.read_file(day_file)
            print(f"Adding {ticker} to database")
            print(f"Adding {len(data)} rows")
            for datum in data:
                if (datum['Open'] == "None"):
                    continue
                if (datum['Volume'] == "None"):
                    datum['Volume'] = 0
                self.cur.execute(self.insert_new, (ticker, datum['Time'], datum['Open'],
                                                   datum['High'], datum['Low'], datum['Close'],
                                                   datum['Volume']))
            print(f"Finished {ticker}")
        print("Still need to commit changes")
