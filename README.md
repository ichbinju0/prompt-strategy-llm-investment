# Prompt Strategy Evaluation for LLM Investment Recommendations

**IE412 AI for Finance — Term Project**
UNIST, Spring 2026

---

## Overview

This project investigates how different prompt design strategies 
affect LLM investment recommendations across three models 
(GPT-5.2, Gemini 3.5 Flash, Claude Sonnet 4.6) and 20 stocks 
from China, Korea, and the US.

**Research Question:**
> Does prompt design matter for LLM investment recommendations? 
> Which prompting strategy leads to the best investment decisions?

---

## Prompt Conditions

| Condition | Strategy | Description |
|-----------|----------|-------------|
| C1 | Baseline | No additional guidance |
| C2 | Role Prompting | Assign objective analyst persona |
| C3 | Metacognitive | Inform model of its own cognitive limitations |
| C4 | Financial Data Injection | Provide actual financial metrics |
| C5 | Chain-of-Thought | Step-by-step structured reasoning |

---

## Dataset

- **20 stocks**: 10 Chinese (NIO, BABA, TCEHY, ...), 
  5 Korean (Samsung, SK Hynix, ...), 5 US (AAPL, MSFT, GOOGL, ...)
- **3 LLM models**: GPT-5.2 Instant, Gemini 3.5 Flash, Claude Sonnet 4.6
- **5 prompt conditions**: C1–C5
- **Total experiments**: 20 × 3 × 5 = 300 responses
- **Market data**: 6-month returns and covariance matrix 
  from yfinance (2025-12-19 to 2026-06-22)

---

## Key Findings

1. **C4 (Financial Data) is the most effective strategy** — 
   the only condition to produce statistically significant score 
   changes (p < 0.001) and positive portfolio returns (+1.72%)

2. **Model confidence varies significantly** — Gemini maintains 
   consistent confidence (Std=2.17) regardless of prompt, while 
   Claude is most sensitive (Std=8.78), especially dropping in C3

3. **CoT paradox** — Chain-of-Thought prompting produces 
   the worst portfolio performance (-3.75%) despite minimal 
   score changes, suggesting structured reasoning may amplify 
   existing biases

4. **LLM predictions are not correlated with actual returns** 
   (r=0.314, p=0.254), but prompt design still affects 
   decision quality (Regret varies from 13.9% to 19.4%)

---

## Results

| Condition | Avg Score | Portfolio Return | Regret |
|-----------|-----------|-----------------|--------|
| C1 Baseline | 1.067 | -1.14% | 16.79% |
| C2 Role | 1.050 | -1.29% | 16.93% |
| C3 Metacognitive | 0.967 | -1.15% | 16.79% |
| C4 Financial Data | 0.467 | **+1.72%** | **13.93%** |
| C5 CoT | 1.083 | -3.75% | 19.39% |

Oracle (perfect foresight): +15.64% | Equal Weight: -13.73%

---

## Figures

| Figure | Description |
|--------|-------------|
| [Fig 1](figures/fig1_country_condition.png) | Average score by country and prompt condition |
| [Fig 2](figures/fig2_score_change.png) | Score change from baseline by prompt strategy |
| [Fig 3](figures/fig3_model_confidence_behavior.png) | Model confidence and response consistency |
| [Fig 4](figures/fig4_confidence_heatmap.png) | Confidence heatmap by model and ticker |
| [Fig 5](figures/fig5_accuracy.png) | LLM baseline score vs actual 6-month return |
| [Fig 6](figures/fig6_dfl_decision_quality.png) | MVO portfolio performance (DFL-inspired) |

---

## Repository Structure
prompt-strategy-llm-investment/

├── README.md

├── analysis.py          # Main analysis code

├── term_project.csv     # Experimental data (LLM responses)

└── figures/

├── fig1_country_condition.png

├── fig2_score_change.png

├── fig3_model_confidence_behavior.png

├── fig4_confidence_heatmap.png

├── fig5_accuracy.png

└── fig6_dfl_decision_quality.png

---

## How to Run

```bash
# Install dependencies
pip install pandas numpy scipy matplotlib yfinance

# Run analysis
python analysis.py
```

> Note: Market data is fetched automatically from yfinance 
> at runtime. Results may differ slightly depending on 
> the execution date.

---

## Methodology

- **Scoring**: Each LLM was asked to rate stocks from 
  -2 (Strong Sell) to +2 (Strong Buy) with a confidence score (0-100)
- **Portfolio optimization**: Mean-Variance Optimization (MVO) 
  using actual covariance matrix estimated from 6-month daily 
  returns (annualized, λ=2.0)
- **Decision quality**: Regret = Oracle return − Portfolio return, 
  inspired by Decision-Focused Learning framework (Lee et al., 2024)

---

## AI Tools Used

This project used Claude (Anthropic) for brainstorming, 
code generation, and writing assistance. All generated code 
was verified by running locally and checking outputs. 
Experimental data was collected manually by the author.

---

## References

- Cao, S., Wang, C., Yi, X. (2025). When LLMs Go Abroad: 
  Foreign Bias in AI Financial Predictions.
- Lee, H. et al. (2025). Your AI, Not Your View: The Bias of 
  LLMs in Investment Analysis. ACM ICAIF.
- Lee, Y. et al. (2024). An Overview of Machine Learning for 
  Portfolio Optimization. Journal of Portfolio Management.
- Ross, J., Lo, A. (2025). One Size Fits None: Heuristic 
  Collapse in LLM Investment Advice.
