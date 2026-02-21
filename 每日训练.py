import pandas as pd
import numpy as np
import akshare as ak
import datetime as dt
import random

print('正在获取A股全市场股票列表...')
all_stocks = []

try:
    stock_info_sh = ak.stock_info_sh_name_code(symbol='主板A股')
    stock_info_sh['上市日期'] = pd.to_datetime(stock_info_sh['上市日期'])
    stock_info_sh['市场'] = 'SH'
    stock_info_sh['代码'] = stock_info_sh['证券代码']
    all_stocks.append(stock_info_sh[['代码', '证券简称', '上市日期', '市场']])
    print(f'获取到上交所主板A股 {len(stock_info_sh)} 只')
except Exception as e:
    print(f'获取上交所主板A股失败: {e}')

try:
    stock_info_sz = ak.stock_info_sz_name_code(symbol='A股列表')
    stock_info_sz['上市日期'] = pd.to_datetime(stock_info_sz['上市日期'])
    stock_info_sz['市场'] = 'SZ'
    stock_info_sz['代码'] = stock_info_sz['A股代码']
    stock_info_sz['证券简称'] = stock_info_sz['A股简称']
    all_stocks.append(stock_info_sz[['代码', '证券简称', '上市日期', '市场']])
    print(f'获取到深交所A股 {len(stock_info_sz)} 只')
except Exception as e:
    print(f'获取深交所A股失败: {e}')

try:
    stock_info_kcb = ak.stock_info_sh_name_code(symbol='科创板')
    stock_info_kcb['上市日期'] = pd.to_datetime(stock_info_kcb['上市日期'])
    stock_info_kcb['市场'] = 'KCB'
    stock_info_kcb['代码'] = stock_info_kcb['证券代码']
    all_stocks.append(stock_info_kcb[['代码', '证券简称', '上市日期', '市场']])
    print(f'获取到科创板 {len(stock_info_kcb)} 只')
except Exception as e:
    print(f'获取科创板失败: {e}')

try:
    stock_info_cyb = ak.stock_info_sz_name_code()
    stock_info_cyb['上市日期'] = pd.to_datetime(stock_info_cyb['上市日期'])
    stock_info_cyb['市场'] = 'CYB'
    stock_info_cyb['代码'] = stock_info_cyb['A股代码']
    stock_info_cyb['证券简称'] = stock_info_cyb['A股简称']
    cyb_codes = stock_info_cyb[stock_info_cyb['A股代码'].str.startswith('3')]
    all_stocks.append(cyb_codes[['代码', '证券简称', '上市日期', '市场']])
    print(f'获取到创业板 {len(cyb_codes)} 只')
except Exception as e:
    print(f'获取创业板失败: {e}')

if not all_stocks:
    print('无法获取股票列表')
else:
    df_stocks = pd.concat(all_stocks, ignore_index=True)
    df_stocks = df_stocks.drop_duplicates(subset=['代码'], keep='first')
    print(f'\n总共获取到 {len(df_stocks)} 只股票')
    
    print('\n正在剔除ST股票...')
    st_pattern = r'^[ST\*]|^SST|^S|^退'
    df_stocks = df_stocks[~df_stocks['证券简称'].str.match(st_pattern, na=False)]
    print(f'剔除ST后剩余: {len(df_stocks)} 只')
    
    print('\n正在剔除上市不满一年的股票...')
    one_year_ago = dt.date.today() - dt.timedelta(days=365)
    df_stocks = df_stocks[df_stocks['上市日期'].dt.date < one_year_ago]
    print(f'剔除上市不满一年后剩余: {len(df_stocks)} 只')
    
    print('\n正在随机选择一只股票...')
    selected = df_stocks.sample(n=1).iloc[0]
    
    stock_code = selected['代码']
    stock_name = selected['证券简称']
    list_date = selected['上市日期']
    market = selected['市场']
    
    if market == 'SH':
        ak_code = 'sh' + stock_code
        full_code = stock_code + '.SH'
    elif market == 'SZ':
        ak_code = 'sz' + stock_code
        full_code = stock_code + '.SZ'
    elif market == 'KCB':
        ak_code = 'sh' + stock_code
        full_code = stock_code + '.SH'
    elif market == 'CYB':
        ak_code = 'sz' + stock_code
        full_code = stock_code + '.SZ'
    else:
        ak_code = stock_code
        full_code = stock_code
    
    valid_start_date = (list_date + pd.Timedelta(days=365)).date()
    today = dt.date.today()
    
    days_between = (today - valid_start_date).days
    if days_between > 0:
        random_days = random.randint(0, days_between)
        random_date = valid_start_date + dt.timedelta(days=random_days)
    else:
        random_date = valid_start_date
    
    print('\n' + '='*60)
    print('随机选中的股票')
    print('='*60)
    print(f'股票代码: {full_code}')
    print(f'股票名称: {stock_name}')
    print(f'上市日期: {list_date.date()}')
    print(f'市场: {market}')
    print(f'AkShare代码: {ak_code}')
    print(f'有效起始日期(上市满一年): {valid_start_date}')
    print(f'有效结束日期: {today}')
    print('-'*60)
    print(f'随机日期: {random_date}')
    print('='*60)
