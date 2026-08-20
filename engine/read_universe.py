"""Read user-provided F&O stocks Excel and normalize symbol list."""
import pandas as pd

path = "/home/ubuntu/upload/NSE_FO_Options_Stocks_List-1.xlsx"
xl = pd.ExcelFile(path)
print("sheets:", xl.sheet_names)
for sheet in xl.sheet_names:
    df = xl.parse(sheet)
    print(f"\n--- {sheet} --- shape={df.shape}")
    print(df.head(10).to_string())
    # Save cleaned list
    col = df.columns[0]
    symbols = [str(s).strip().upper() for s in df[col].dropna().unique()]
    symbols = [s for s in symbols if s]
    print("count:", len(symbols))
    print("first 20:", symbols[:20])
