import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

import akshare as ak
import datetime as dt

end_date = dt.date.today().strftime('%Y%m%d')
start_date = (dt.date.today() - dt.timedelta(days=365)).strftime('%Y%m%d')

stock_code = "000001.SZ"

code_up = stock_code.upper()
if code_up.endswith('.SZ'):
    ak_code = 'sz' + code_up.split('.')[0]
elif code_up.endswith('.SH'):
    ak_code = 'sh' + code_up.split('.')[0]
elif len(code_up) == 6 and code_up.isdigit():
    ak_code = ('sh' if code_up.startswith('6') else 'sz') + code_up
elif code_up.startswith(('SZ', 'SH')):
    ak_code = code_up.lower()
else:
    ak_code = code_up.lower()

try:
    df = ak.stock_zh_a_daily(symbol=ak_code, start_date=start_date, end_date=end_date, adjust='qfq')
except Exception as e:
    print('获取数据失败：', e)
    raise SystemExit(1)

if df is None or df.empty:
    print('未获取到数据，请检查股票代码或网络')
else:
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    elif '日期' in df.columns:
        df['date'] = pd.to_datetime(df['日期'])
        df = df.sort_values('日期')
    print(df)

def rolling_rank(series, window):
    result = np.full(len(series), np.nan)
    for i in range(window - 1, len(series)):
        window_data = series.iloc[i - window + 1: i + 1]
        ranks = window_data.rank(method='first')
        result[i] = ranks.iloc[-1]
    return pd.Series(result, index=series.index)

df['rank_open'] = rolling_rank(df['open'], 10)
df['rank_volume'] = rolling_rank(df['volume'], 10)

def rolling_corr(s1, s2, window):
    return s1.rolling(window=window, min_periods=window).corr(s2)

df['factor'] = -1 * rolling_corr(df['rank_open'], df['rank_volume'], 10)

df['fwd_ret'] = df['close'].shift(-20) / df['close'] - 1

df_ic = df[['date', 'factor', 'fwd_ret']].dropna()

if len(df_ic) >= 3:
    rank_ic = df_ic['factor'].corr(df_ic['fwd_ret'], method='spearman')
    pearson_ic = df_ic['factor'].corr(df_ic['fwd_ret'])
else:
    rank_ic = float('nan')
    pearson_ic = float('nan')

df_ic['month'] = df_ic['date'].dt.to_period('M')
monthly_ic = df_ic.groupby('month').apply(
    lambda x: x['factor'].corr(x['fwd_ret'], method='spearman') if len(x) >= 3 else np.nan
)
monthly_ic = monthly_ic.dropna()

if len(monthly_ic) >= 2:
    ic_mean = monthly_ic.mean()
    ic_std = monthly_ic.std()
    ic_ir = ic_mean / ic_std if ic_std != 0 else np.nan
    
    # T统计量计算
    n = len(monthly_ic)
    if n >= 2 and ic_std != 0:
        t_stat = ic_mean / (ic_std / np.sqrt(n))
        p_value = stats.t.sf(np.abs(t_stat), n-1) * 2  # 双尾检验
    else:
        t_stat = float('nan')
        p_value = float('nan')
else:
    ic_mean = rank_ic
    ic_std = float('nan')
    ic_ir = float('nan')
    t_stat = float('nan')
    p_value = float('nan')

print('因子: -1 * correlation(rank(open), rank(volume), 10)')
print('IC_spearman:', rank_ic)
print('IC_pearson:', pearson_ic)
print('IC_mean (月度):', ic_mean)
print('IC_std (月度):', ic_std)
print('IC_IR:', ic_ir)
print('T-statistic:', t_stat)
print('P-value:', p_value)

if not df_ic.empty:
    x = df_ic['factor']
    y = df_ic['fwd_ret']
    sxx = ((x - x.mean())**2).sum()
    sxy = ((x - x.mean()) * (y - y.mean())).sum()
    slope = (sxy / sxx) if sxx != 0 else 0
    intercept = y.mean() - slope * x.mean()
    fig_ic, ax_ic = plt.subplots(figsize=(8, 6))
    ax_ic.scatter(x, y, s=14, alpha=0.6, color='#1f77b4', edgecolors='none')
    x_line = pd.Series([x.min(), x.max()])
    ax_ic.plot(x_line, slope * x_line + intercept, color='#ff7f0e', linewidth=1)
    ax_ic.set_title(f'IC收益率散点图: {stock_code}  (Spearman={rank_ic:.3f}, Pearson={pearson_ic:.3f})')
    ax_ic.set_xlabel('因子值')
    ax_ic.set_ylabel('20日未来收益')
else:
    print('有效样本不足，无法绘制IC散点图')

df['MA5']  = df['close'].rolling(window=5).mean()
df['MA10'] = df['close'].rolling(window=10).mean()
df['MA20'] = df['close'].rolling(window=20).mean()

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_yscale('log')

for idx, row in df.iterrows():
    color = 'red' if row['close'] >= row['open'] else 'green'
    ax.plot([row.name, row.name], [row['low'], row['high']], color='black', linewidth=0.8)
    body_bottom = min(row['open'], row['close'])
    body_height = abs(row['open'] - row['close'])
    ax.bar(row.name, body_height, bottom=body_bottom, width=0.6,
           color=color, edgecolor='black')

ax.plot(df.index, df['MA5'],  label='MA5',  linewidth=1)
ax.plot(df.index, df['MA10'], label='MA10', linewidth=1)
ax.plot(df.index, df['MA20'], label='MA20', linewidth=1)

ax.set_title(f'{stock_code} 最近一年K线图')
ax.set_ylabel('价格（元）')
ax.legend()

fig.autofmt_xdate()

plt.tight_layout()
plt.show()
