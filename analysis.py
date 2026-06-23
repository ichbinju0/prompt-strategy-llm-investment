import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import minimize
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import yfinance as yf

# --- Data Loading ---
df = pd.read_csv(r'C:\Users\hahal\Desktop\Programming\term_project\term_project.csv')
df = df.dropna(subset=['Ticker'])

colors = {
    'China': '#E05C5C', 'Korea': '#4A90D9', 'US': '#5BAD6F',
    'GPT-5.2 Instant':   '#F4845F',
    'Gemini 3.5 Flash':  '#4285F4',
    'Claude Sonnet 4.6': '#A076C8'
}
countries        = ['China', 'Korea', 'US']
models           = ['GPT-5.2 Instant', 'Gemini 3.5 Flash', 'Claude Sonnet 4.6']
short_model      = ['GPT-5.2', 'Gemini 3.5', 'Claude 4.6']
model_colors     = [colors[m] for m in models]
score_cols       = ['C1_Score', 'C2_Score', 'C3_Score', 'C4_Score', 'C5_Score']
conf_cols        = ['C1_Conf',  'C2_Conf',  'C3_Conf',  'C4_Conf',  'C5_Conf']
cond_labels      = ['C1\nBaseline', 'C2\nRole\nPrompt',
                    'C3\nMetacognitive', 'C4\nFinancial\nData', 'C5\nChain-of-\nThought']
cond_labels_short = ['C1', 'C2', 'C3', 'C4', 'C5']

# --- Fetch actual market data (covariance + 6M returns) ---
tickers_cn  = ['NIO','TME','BABA','JD','PDD','XPEV','TCEHY','LI','BIDU','NTES']
tickers_us  = ['AAPL','MSFT','GOOGL','META','AMZN']
tickers_all = tickers_cn + tickers_us

print("[Output] Fetching market data from yfinance...")
prices        = yf.download(tickers_all, period='6mo', auto_adjust=True, progress=False)['Close']
daily_returns = prices.pct_change().dropna()[tickers_all]
cov_matrix    = daily_returns.cov().values * 252  # annualized

returns_6m = {t: round((prices[t].dropna().iloc[-1] - prices[t].dropna().iloc[0])
                        / prices[t].dropna().iloc[0] * 100, 1) for t in tickers_all}
df['Return_6M'] = df['Ticker'].map(returns_6m)
actual_returns  = np.array([returns_6m[t] for t in tickers_all]) / 100

# Score scaling: based on actual return std
ret_std      = np.std(list(returns_6m.values())) / 100
score_scale  = ret_std / 2
data_start   = prices.index[0].strftime('%Y-%m-%d')
data_end     = prices.index[-1].strftime('%Y-%m-%d')
print(f"[Output] Market data: {data_start} to {data_end}")
print(f"[Output] Score scaling factor: {score_scale:.4f} (based on actual return std={ret_std*100:.2f}%)")

# ============================================================
# PART 1. PROMPT STRATEGY COMPARISON
# ============================================================

# --- Figure 1: Average Investment Score by Country and Prompt Condition ---
fig1, ax1 = plt.subplots(figsize=(12, 5.5))
x = np.arange(len(score_cols))
width = 0.26

for i, country in enumerate(countries):
    sub   = df[df['Country'] == country]
    means = [sub[c].mean() for c in score_cols]
    bars  = ax1.bar(x + i*width, means, width, label=country,
                    color=colors[country], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, means):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=7.5, fontweight='500')

ax1.set_xticks(x + width)
ax1.set_xticklabels(cond_labels, fontsize=9)
ax1.set_ylabel('Average Investment Score', fontsize=11)
ax1.set_title('Figure 1. Average LLM Investment Score by Country and Prompt Condition',
              fontsize=12, fontweight='bold', pad=12)
ax1.legend(title='Country', fontsize=10)
ax1.set_ylim(-0.3, 1.9)
ax1.axhline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.5)
ax1.grid(axis='y', alpha=0.3)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('fig1_country_condition.png', dpi=150, bbox_inches='tight')
plt.close()
print("[Output] Figure 1 saved: fig1_country_condition.png")

# --- Figure 2: Score Change from Baseline (C1) by Prompt Strategy ---
fig2, axes = plt.subplots(1, 2, figsize=(13, 5))
compare_cols   = ['C2_Score', 'C3_Score', 'C4_Score', 'C5_Score']
compare_labels = ['C2\nRole', 'C3\nMetacognitive', 'C4\nData', 'C5\nCoT']
x     = np.arange(len(compare_cols))
width = 0.26

# 2a: By Country
ax2a = axes[0]
for i, country in enumerate(countries):
    sub   = df[df['Country'] == country]
    c1    = sub['C1_Score'].mean()
    diffs = [sub[c].mean() - c1 for c in compare_cols]
    bars  = ax2a.bar(x + i*width, diffs, width, label=country,
                     color=colors[country], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, diffs):
        ax2a.text(bar.get_x()+bar.get_width()/2,
                  bar.get_height() + (0.01 if val >= 0 else -0.04),
                  f'{val:+.2f}', ha='center', va='bottom', fontsize=7.5, fontweight='500')

ax2a.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax2a.set_xticks(x + width)
ax2a.set_xticklabels(compare_labels, fontsize=10)
ax2a.set_ylabel('Score Change from C1 Baseline', fontsize=10)
ax2a.set_title('(a) Score Change by Country', fontsize=11, fontweight='bold')
ax2a.legend(title='Country', fontsize=9)
ax2a.grid(axis='y', alpha=0.3)
ax2a.spines['top'].set_visible(False)
ax2a.spines['right'].set_visible(False)

# 2b: By Model
ax2b = axes[1]
for i, model in enumerate(models):
    sub   = df[df['Model'] == model]
    c1    = sub['C1_Score'].mean()
    diffs = [sub[c].mean() - c1 for c in compare_cols]
    bars  = ax2b.bar(x + i*width, diffs, width, label=short_model[i],
                     color=model_colors[i], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, diffs):
        ax2b.text(bar.get_x()+bar.get_width()/2,
                  bar.get_height() + (0.01 if val >= 0 else -0.04),
                  f'{val:+.2f}', ha='center', va='bottom', fontsize=7.5, fontweight='500')

ax2b.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax2b.set_xticks(x + width)
ax2b.set_xticklabels(compare_labels, fontsize=10)
ax2b.set_ylabel('Score Change from C1 Baseline', fontsize=10)
ax2b.set_title('(b) Score Change by Model', fontsize=11, fontweight='bold')
ax2b.legend(title='Model', fontsize=9)
ax2b.grid(axis='y', alpha=0.3)
ax2b.spines['top'].set_visible(False)
ax2b.spines['right'].set_visible(False)

fig2.suptitle('Figure 2. Score Change from Baseline (C1) by Prompt Strategy',
              fontsize=12, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('fig2_score_change.png', dpi=150, bbox_inches='tight')
plt.close()
print("[Output] Figure 2 saved: fig2_score_change.png")

# ============================================================
# PART 2. MODEL BEHAVIOR ANALYSIS
# ============================================================

# --- Figure 3: Model Confidence Behavior ---
fig3, axes = plt.subplots(1, 2, figsize=(13, 5))

# 3a: Average Confidence by Model x Condition
ax3a = axes[0]
x     = np.arange(len(conf_cols))
width = 0.26

for i, model in enumerate(models):
    sub   = df[df['Model'] == model]
    confs = [sub[c].mean() for c in conf_cols]
    bars  = ax3a.bar(x + i*width, confs, width, label=short_model[i],
                     color=model_colors[i], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, confs):
        ax3a.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                  f'{val:.1f}', ha='center', va='bottom', fontsize=7, fontweight='500')

ax3a.set_xticks(x + width)
ax3a.set_xticklabels(cond_labels_short, fontsize=11)
ax3a.set_ylabel('Average Confidence Score', fontsize=10)
ax3a.set_title('(a) Average Confidence by Model and Condition',
               fontsize=11, fontweight='bold')
ax3a.legend(title='Model', fontsize=9)
ax3a.set_ylim(0, 100)
ax3a.grid(axis='y', alpha=0.3)
ax3a.spines['top'].set_visible(False)
ax3a.spines['right'].set_visible(False)

# 3b: Response Variability
ax3b = axes[1]
conf_stds  = [df[df['Model']==m][conf_cols].apply(lambda r: r.std(), axis=1).mean() for m in models]
score_stds = [df[df['Model']==m][score_cols].apply(lambda r: r.std(), axis=1).mean() for m in models]

x2     = np.arange(3)
width2 = 0.35
bars1  = ax3b.bar(x2 - width2/2, conf_stds,  width2, label='Confidence Std',
                   color=model_colors, alpha=0.85, edgecolor='white')
bars2  = ax3b.bar(x2 + width2/2, score_stds, width2, label='Score Std',
                   color=model_colors, alpha=0.45, edgecolor='white', hatch='//')
for bar, val in zip(bars1, conf_stds):
    ax3b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
              f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='600')
for bar, val in zip(bars2, score_stds):
    ax3b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
              f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='600')

ax3b.set_xticks(x2)
ax3b.set_xticklabels(short_model, fontsize=10)
ax3b.set_ylabel('Average Row Std across C1-C5', fontsize=10)
ax3b.set_title('(b) Response Variability by Model\n(Lower = More Consistent across Prompts)',
               fontsize=11, fontweight='bold')
ax3b.legend(fontsize=9)
ax3b.grid(axis='y', alpha=0.3)
ax3b.spines['top'].set_visible(False)
ax3b.spines['right'].set_visible(False)

fig3.suptitle('Figure 3. Model Confidence and Response Consistency across Prompt Conditions',
              fontsize=12, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('fig3_model_confidence_behavior.png', dpi=150, bbox_inches='tight')
plt.close()
print("[Output] Figure 3 saved: fig3_model_confidence_behavior.png")

# --- Figure 4: Confidence Heatmap ---
fig4, axes = plt.subplots(1, 3, figsize=(14, 4.5))

for i, model in enumerate(models):
    ax  = axes[i]
    sub = df[df['Model'] == model].copy()
    ticker_order = sub.groupby('Ticker')['C1_Conf'].mean().sort_values(ascending=False).index.tolist()
    pivot = sub.set_index('Ticker')[conf_cols].loc[ticker_order]
    pivot.columns = cond_labels_short

    im = ax.imshow(pivot.values, aspect='auto', cmap='RdYlGn', vmin=30, vmax=100)
    ax.set_xticks(range(5))
    ax.set_xticklabels(cond_labels_short, fontsize=10)
    ax.set_yticks(range(len(ticker_order)))
    ax.set_yticklabels(ticker_order, fontsize=8)
    ax.set_title(f'{short_model[i]}', fontsize=11, fontweight='bold')

    for r in range(len(ticker_order)):
        for c in range(5):
            ax.text(c, r, f'{pivot.values[r, c]:.0f}',
                    ha='center', va='center', fontsize=7,
                    color='black' if 40 < pivot.values[r, c] < 85 else 'white')

plt.colorbar(im, ax=axes[-1], label='Confidence Score', shrink=0.8)
fig4.suptitle('Figure 4. Confidence Score Heatmap by Model, Ticker, and Prompt Condition',
              fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('fig4_confidence_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("[Output] Figure 4 saved: fig4_confidence_heatmap.png")

# ============================================================
# PART 3. PREDICTION ACCURACY & DECISION QUALITY
# ============================================================

# --- Figure 5: LLM Baseline Score vs. Actual 6-Month Return ---
df_ret     = df[df['Return_6M'].notna()].copy()
ticker_avg = df_ret.groupby(['Ticker', 'Country']).agg(
    C1_mean=('C1_Score', 'mean'),
    Return_6M=('Return_6M', 'first')
).reset_index()

fig5, ax5 = plt.subplots(figsize=(8, 5.5))
for country in ['China', 'US']:
    sub = ticker_avg[ticker_avg['Country'] == country]
    ax5.scatter(sub['C1_mean'], sub['Return_6M'],
                color=colors[country], s=80, alpha=0.85, label=country,
                zorder=3, edgecolors='white', linewidth=0.5)
    for _, row in sub.iterrows():
        ax5.annotate(row['Ticker'], (row['C1_mean'], row['Return_6M']),
                     textcoords='offset points', xytext=(6, 3),
                     fontsize=7.5, color=colors[country])

x_all = ticker_avg['C1_mean'].values
y_all = ticker_avg['Return_6M'].values
slope, intercept, r, p, se = stats.linregress(x_all, y_all)
x_line = np.linspace(x_all.min()-0.1, x_all.max()+0.1, 100)
ax5.plot(x_line, slope*x_line+intercept, 'gray', linewidth=1.5, linestyle='--', alpha=0.7)
ax5.text(0.05, 0.95, f'r = {r:.3f}, p = {p:.3f}',
         transform=ax5.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))
ax5.axhline(0, color='gray', linewidth=0.6, linestyle=':')
ax5.axvline(0, color='gray', linewidth=0.6, linestyle=':')
ax5.set_xlabel('Average C1 Baseline Score (LLM Prediction)', fontsize=11)
ax5.set_ylabel('Actual 6-Month Return (%)', fontsize=11)
ax5.set_title('Figure 5. LLM Baseline Score vs. Actual 6-Month Stock Return',
              fontsize=12, fontweight='bold', pad=10)
ax5.legend(fontsize=10)
ax5.grid(alpha=0.25)
ax5.spines['top'].set_visible(False)
ax5.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('fig5_accuracy.png', dpi=150, bbox_inches='tight')
plt.close()
print("[Output] Figure 5 saved: fig5_accuracy.png")

# --- Figure 6: MVO Portfolio Performance (DFL-Inspired) ---
def mvo_portfolio(expected_returns, cov_matrix, lam=2.0):
    """
    MVO: max w^T mu - lambda * w^T Sigma w
    - Covariance matrix: estimated from 6-month daily returns (annualized, *252)
    - Lambda = 2.0: moderate risk aversion
    - Score scaling: based on actual return std (score_scale = ret_std / 2)
    - Long-only constraint: w >= 0
    """
    n = len(expected_returns)

    def neg_utility(w):
        return -(w @ expected_returns - lam * w @ cov_matrix @ w)

    def neg_utility_grad(w):
        return -(expected_returns - 2 * lam * cov_matrix @ w)

    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds      = [(0, 1)] * n
    w0          = np.ones(n) / n
    result = minimize(neg_utility, w0, method='SLSQP',
                      bounds=bounds, constraints=constraints,
                      jac=neg_utility_grad,
                      options={'ftol': 1e-9, 'maxiter': 1000})
    return result.x

def portfolio_return(weights, actual_returns):
    return weights @ actual_returns

conditions_map = {
    'C1 (Baseline)':       'C1_Score',
    'C2 (Role)':           'C2_Score',
    'C3 (Metacognitive)':  'C3_Score',
    'C4 (Financial Data)': 'C4_Score',
    'C5 (CoT)':            'C5_Score',
}
cond_order = list(conditions_map.keys())

df_dfl     = df[df['Ticker'].isin(tickers_all)].copy()
w_oracle   = mvo_portfolio(actual_returns, cov_matrix)
ret_oracle = portfolio_return(w_oracle, actual_returns)
w_equal    = np.ones(len(tickers_all)) / len(tickers_all)
ret_equal  = portfolio_return(w_equal, actual_returns)

results_dfl = []
for model in models:
    for cond_label, cond_col in conditions_map.items():
        sub    = df_dfl[df_dfl['Model'] == model]
        scores = [float(sub[sub['Ticker']==t][cond_col].values[0])
                  if len(sub[sub['Ticker']==t]) > 0 else 0.0 for t in tickers_all]
        expected_ret_proxy = np.array(scores) * score_scale
        w        = mvo_portfolio(expected_ret_proxy, cov_matrix)
        port_ret = portfolio_return(w, actual_returns)
        results_dfl.append({
            'Model': model, 'Condition': cond_label,
            'Portfolio_Return': port_ret * 100,
            'Regret':   (ret_oracle - port_ret) * 100,
            'vs_Equal': (port_ret - ret_equal)  * 100
        })

results_dfl_df = pd.DataFrame(results_dfl)

fig6, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# 6a: Average portfolio return by condition
ax6a       = axes[0]
cond_avg   = results_dfl_df.groupby('Condition')['Portfolio_Return'].mean().reindex(cond_order)
bar_colors = ['#E05C5C','#F4845F','#A076C8','#4A90D9','#5BAD6F']
bars = ax6a.bar(range(5), cond_avg.values,
                color=bar_colors, alpha=0.85, edgecolor='white', width=0.55)
for bar, val in zip(bars, cond_avg.values):
    ax6a.text(bar.get_x()+bar.get_width()/2,
              bar.get_height() + (0.1 if val >= 0 else -0.5),
              f'{val:.2f}%', ha='center', va='bottom', fontsize=9, fontweight='600')
ax6a.axhline(ret_equal*100, color='gray', linewidth=1.5, linestyle='--', alpha=0.8,
             label=f'Equal Weight ({ret_equal*100:.2f}%)')
ax6a.axhline(ret_oracle*100, color='gold', linewidth=1.5, linestyle='--', alpha=0.9,
             label=f'Oracle ({ret_oracle*100:.2f}%)')
ax6a.set_xticks(range(5))
ax6a.set_xticklabels(['C1\nBaseline','C2\nRole','C3\nMeta-\ncognitive',
                       'C4\nData','C5\nCoT'], fontsize=9)
ax6a.set_ylabel('Portfolio Return (%)', fontsize=10)
ax6a.set_title('(a) Avg Portfolio Return by Prompt Condition', fontsize=11, fontweight='bold')
ax6a.legend(fontsize=8)
ax6a.grid(axis='y', alpha=0.3)
ax6a.spines['top'].set_visible(False)
ax6a.spines['right'].set_visible(False)

# 6b: Regret by model x condition
ax6b  = axes[1]
x     = np.arange(5)
width = 0.26

for i, model in enumerate(models):
    sub     = results_dfl_df[results_dfl_df['Model']==model]
    sub     = sub.set_index('Condition').reindex(cond_order)
    regrets = sub['Regret'].values
    bars    = ax6b.bar(x + i*width, regrets, width, label=short_model[i],
                       color=model_colors[i], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, regrets):
        ax6b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                  f'{val:.1f}', ha='center', va='bottom', fontsize=6.5)

ax6b.set_xticks(x + width)
ax6b.set_xticklabels(['C1','C2','C3','C4','C5'], fontsize=11)
ax6b.set_ylabel('Regret = Oracle - Portfolio Return (%)', fontsize=9)
ax6b.set_title('(b) MVO Regret by Model and Condition\n(Lower = Better Decision Quality)',
               fontsize=11, fontweight='bold')
ax6b.legend(fontsize=9)
ax6b.grid(axis='y', alpha=0.3)
ax6b.spines['top'].set_visible(False)
ax6b.spines['right'].set_visible(False)

fig6.suptitle('Figure 6. DFL-Inspired Decision Quality: MVO Portfolio Performance\nunder Five Prompt Conditions',
              fontsize=12, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('fig6_dfl_decision_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print("[Output] Figure 6 saved: fig6_dfl_decision_quality.png")

# ============================================================
# STATISTICAL ANALYSIS SUMMARY
# ============================================================
print("\n" + "="*60)
print("  STATISTICAL ANALYSIS SUMMARY")
print("="*60)

print(f"\n[Data] Market data period : {data_start} to {data_end} (yfinance)")
print(f"[Data] Score scaling factor: {score_scale:.4f} (ret_std={ret_std*100:.2f}%)")
print(f"[Data] Covariance matrix   : 15x15, annualized from 6-month daily returns")

print("\n[1] Average Score by Prompt Condition (All Models)")
print(f"  {'Condition':<22} {'Mean':>6} {'Std':>6}")
print("  " + "-"*36)
cond_names = ['C1 Baseline','C2 Role','C3 Metacognitive','C4 Financial Data','C5 CoT']
for col, name in zip(score_cols, cond_names):
    print(f"  {name:<22} {df[col].mean():>6.3f} {df[col].std():>6.3f}")

print("\n[2] One-way ANOVA: Score difference across C1-C5")
f_stat, p_anova = stats.f_oneway(*[df[c] for c in score_cols])
print(f"  F = {f_stat:.3f}, p = {p_anova:.4f} {'[significant]' if p_anova<0.05 else '[not significant]'}")

print("\n[3] Paired t-test: C1 vs Each Condition")
for col, name in zip(score_cols[1:], cond_names[1:]):
    t, p = stats.ttest_rel(df['C1_Score'], df[col])
    diff = df['C1_Score'].mean() - df[col].mean()
    print(f"  C1 vs {name:<20} delta={diff:+.3f}  p={p:.4f} {'[significant]' if p<0.05 else '[not significant]'}")

print("\n[4] Model Confidence Analysis")
print(f"  {'Model':<22} {'Avg Conf':>9} {'Conf Std':>9} {'Score Std':>10}")
print("  " + "-"*54)
for model in models:
    sub       = df[df['Model'] == model]
    avg_conf  = sub[conf_cols].values.mean()
    conf_std  = sub[conf_cols].apply(lambda r: r.std(), axis=1).mean()
    score_std = sub[score_cols].apply(lambda r: r.std(), axis=1).mean()
    print(f"  {model:<22} {avg_conf:>9.2f} {conf_std:>9.4f} {score_std:>10.4f}")

print("\n[5] One-way ANOVA: Confidence difference across Models")
groups   = [df[df['Model']==m][conf_cols].values.flatten() for m in models]
f2, p2   = stats.f_oneway(*groups)
print(f"  F = {f2:.3f}, p = {p2:.4f} {'[significant]' if p2<0.05 else '[not significant]'}")
print("\n  Pairwise t-test (Confidence):")
for i in range(len(models)):
    for j in range(i+1, len(models)):
        g1   = df[df['Model']==models[i]][conf_cols].values.flatten()
        g2   = df[df['Model']==models[j]][conf_cols].values.flatten()
        t, p = stats.ttest_ind(g1, g2)
        print(f"  {models[i].split()[0]} vs {models[j].split()[0]}: "
              f"t={t:.3f}, p={p:.4f} {'[significant]' if p<0.05 else '[not significant]'}")

print("\n[6] C1 Score vs Actual 6-Month Return — Pearson Correlation")
t_avg = df_ret.groupby('Ticker').agg(
    C1_mean=('C1_Score','mean'), Return_6M=('Return_6M','first')).reset_index()
r, p  = stats.pearsonr(t_avg['C1_mean'], t_avg['Return_6M'])
print(f"  Pearson r = {r:.4f}, p = {p:.4f} {'[significant]' if p<0.05 else '[not significant]'}")

print("\n[7] DFL Decision Quality Summary")
print(f"  Oracle (MVO with actual returns, annualized cov): {ret_oracle*100:.2f}%")
print(f"  Equal Weight benchmark                          : {ret_equal*100:.2f}%")
print(f"\n  {'Condition':<25} {'Avg Return':>11} {'vs Equal':>10} {'Regret':>10}")
print("  " + "-"*58)
for cond in cond_order:
    sub = results_dfl_df[results_dfl_df['Condition']==cond]
    print(f"  {cond:<25} {sub['Portfolio_Return'].mean():>10.2f}% "
          f"{sub['vs_Equal'].mean():>9.2f}% {sub['Regret'].mean():>9.2f}%")

print("\n[Output] All analysis complete. Figures saved: fig1 to fig6.")