import pandas as pd, numpy as np
from scipy import stats

df = pd.read_csv("/Users/dylanmurphy/Library/CloudStorage/OneDrive-UniversityOfOregon/Thesis/PM2.5-weather/data/processed/analysis_data.csv", parse_dates=['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)
df['date'] = df['timestamp'].dt.date

daily = df.groupby('date').agg(
    t_max=('temperature_f','max'),
    t_min=('temperature_f','min'),
    t_mean=('temperature_f','mean'),
    rh_mean=('humidity','mean'),
    pm25_mean=('pm2.5_lrapa','mean'),
    n_hrs=('temperature_f','count')
).reset_index()
daily['dtr'] = daily['t_max'] - daily['t_min']
daily = daily[daily['n_hrs'] >= 18]
daily['is_smoke'] = daily['pm25_mean'] >= 35

sm = daily[daily['is_smoke']]
cl = daily[~daily['is_smoke']]
print(f"Days: {len(daily)} | smoke(mean>=35): {len(sm)} | clean: {len(cl)}")
print()

for col, lab in [('dtr','DTR (F)'),('t_max','T_max (F)'),('t_min','T_min (F)'),('t_mean','T_mean (F)'),('rh_mean','RH (%)')]:
    s, c = sm[col].mean(), cl[col].mean()
    _, p = stats.ttest_ind(sm[col].dropna(), cl[col].dropna(), equal_var=False)
    r, rp = stats.pearsonr(daily[col], daily['pm25_mean'])
    print(f"{lab:14s}  smoke={s:5.1f}  clean={c:5.1f}  diff={s-c:+5.1f}  t-test_p={p:.3f}  r={r:+.3f}  r_p={rp:.3f}")
