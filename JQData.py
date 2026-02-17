from jqdatasdk import *
import matplotlib.pyplot as plt
import pandas as pd
auth('13120283865', '237890WEUIop')

# count=get_query_count()
# print(count)
# 000852.XSHG
df = get_bars('000852.XSHG', unit='1d', fields=[
              'date', 'open', 'high', 'low', 'close'], include_now=False, start_dt="2024-09-18", end_dt='2025-09-25')
print(df)

# 绘制close price曲线
df['date'] = pd.to_datetime(df['date'])
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['close'], linewidth=1.5)
plt.title('Close Price - 000852.XSHG', fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Close Price', fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
