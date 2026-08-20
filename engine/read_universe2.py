"""Parse the names column properly (skip serial numbers) and build NSE symbol map."""
import json
import pandas as pd

path = "/home/ubuntu/upload/NSE_FO_Options_Stocks_List-1.xlsx"
df = pd.read_excel(path)
print(df.head(5).to_string())
print(df.tail(5).to_string())
print("dtypes:", df.dtypes.to_dict())
print("nulls:", df.isnull().sum().to_dict())
