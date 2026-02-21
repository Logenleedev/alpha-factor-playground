import pandas as pd
import numpy as np
import akshare as ak
import datetime as dt
import time

end_date = dt.date.today().strftime('%Y%m%d')
start_date = (dt.date.today() - dt.timedelta(days=365)).strftime('%Y%m%d')

print('正在获取中证1000成分股列表...')
try:
    stock_pool_df = ak.index_stock_cons(symbol="000852")
    print(f'列名: {stock_pool_df.columns.tolist()}')
    
    if '品种代码' in stock_pool_df.columns:
        stock_pool = stock_pool_df['品种代码'].tolist()
    elif '代码' in stock_pool_df.columns:
        stock_pool = stock_pool_df['代码'].tolist()
    else:
        stock_pool = stock_pool_df.iloc[:, 0].tolist()
    
    print(f'获取到 {len(stock_pool)} 只中证1000成分股')
except Exception as e:
    print(f'获取中证1000成分股失败: {e}')
    stock_pool = []

print('\n正在获取股票上市日期...')
list_date_dict = {}

try:
    stock_info_sh = ak.stock_info_sh_name_code(symbol='主板A股')
    stock_info_sh['上市日期'] = pd.to_datetime(stock_info_sh['上市日期'])
    for _, row in stock_info_sh.iterrows():
        list_date_dict[row['证券代码']] = row['上市日期']
    print(f'获取到上交所主板A股 {len(stock_info_sh)} 只')
except Exception as e:
    print(f'获取上交所主板A股失败: {e}')

try:
    stock_info_sz = ak.stock_info_sz_name_code(symbol='A股列表')
    stock_info_sz['上市日期'] = pd.to_datetime(stock_info_sz['上市日期'])
    for _, row in stock_info_sz.iterrows():
        list_date_dict[row['A股代码']] = row['上市日期']
    print(f'获取到深交所A股 {len(stock_info_sz)} 只')
except Exception as e:
    print(f'获取深交所A股失败: {e}')

try:
    stock_info_kcb = ak.stock_info_sh_name_code(symbol='科创板')
    stock_info_kcb['上市日期'] = pd.to_datetime(stock_info_kcb['上市日期'])
    for _, row in stock_info_kcb.iterrows():
        list_date_dict[row['证券代码']] = row['上市日期']
    print(f'获取到科创板 {len(stock_info_kcb)} 只')
except Exception as e:
    print(f'获取科创板失败: {e}')

try:
    stock_info_cyb = ak.stock_info_sz_name_code(symbol='创业板列表')
    stock_info_cyb['上市日期'] = pd.to_datetime(stock_info_cyb['上市日期'])
    for _, row in stock_info_cyb.iterrows():
        list_date_dict[row['A股代码']] = row['上市日期']
    print(f'获取到创业板 {len(stock_info_cyb)} 只')
except Exception as e:
    print(f'获取创业板失败: {e}')

print(f'\n总共获取到 {len(list_date_dict)} 只股票的上市日期')

def convert_code(stock_code):
    stock_code = str(stock_code).strip()
    if '.' in stock_code:
        return stock_code.lower().replace('.sz', 'sz').replace('.sh', 'sh')
    else:
        if stock_code.startswith('6'):
            return 'sh' + stock_code
        else:
            return 'sz' + stock_code

def get_list_date(stock_code):
    code = str(stock_code).strip()
    if '.' in code:
        code = code.split('.')[0]
    if code in list_date_dict:
        return list_date_dict[code]
    return None

def get_stock_data(stock_code):
    ak_code = convert_code(stock_code)
    
    try:
        df = ak.stock_zh_a_daily(symbol=ak_code, start_date=start_date, end_date=end_date, adjust='qfq')
        if df is not None and not df.empty:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif '日期' in df.columns:
                df['date'] = pd.to_datetime(df['日期'])
            df = df.sort_values('date')
            df['stock_code'] = stock_code
            return df
    except Exception as e:
        return None
    return None

if not stock_pool:
    print('无法获取股票池，程序退出')
else:
    print('\n开始获取股票池数据...')
    all_data = []
    failed_stocks = []
    
    for i, stock_code in enumerate(stock_pool, 1):
        if i % 100 == 0:
            print(f'进度: {i}/{len(stock_pool)}...')
        
        stock_data = get_stock_data(stock_code)
        if stock_data is not None:
            all_data.append(stock_data)
        else:
            failed_stocks.append(stock_code)
        
        time.sleep(0.1)
    
    if not all_data:
        print('未获取到任何股票数据')
    else:
        df_all = pd.concat(all_data, ignore_index=True)
        
        print(f'\n原始数据概览:')
        print(f'总行数: {len(df_all)}')
        print(f'股票数: {df_all["stock_code"].nunique()}')
        
        print('\n开始筛选数据...')
        
        df_all['list_date'] = df_all['stock_code'].apply(lambda x: get_list_date(x))
        
        no_list_date = df_all['list_date'].isna().sum()
        df_all = df_all.dropna(subset=['list_date'])
        print(f'无上市日期的数据: {no_list_date} 行')
        
        df_all['days_listed'] = (df_all['date'] - df_all['list_date']).dt.days
        
        before_filter = len(df_all)
        df_all = df_all[df_all['days_listed'] >= 365].copy()
        after_filter = len(df_all)
        print(f'剔除上市未满一年的数据: {before_filter - after_filter} 行')
        
        before_filter = len(df_all)
        df_all = df_all[df_all['close'] > 0].copy()
        after_filter = len(df_all)
        print(f'剔除ST/停牌数据(收盘价为0): {before_filter - after_filter} 行')
        
        print(f'\n筛选后数据概览:')
        print(f'总行数: {len(df_all)}')
        print(f'股票数: {df_all["stock_code"].nunique()}')
        print(f'日期范围: {df_all["date"].min()} ~ {df_all["date"].max()}')
        
        output_path = '/Users/mac/Desktop/code /因子/playground/中证1000_k线数据.csv'
        df_all.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f'\n数据已保存到: {output_path}')
        
        print('\n数据样例:')
        print(df_all[['date', 'stock_code', 'open', 'close', 'high', 'low', 'volume', 'list_date', 'days_listed']].head(10))
