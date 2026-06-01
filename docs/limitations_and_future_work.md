# Limitations and Future Work

This document summarizes the known limitations of the 0050 vs TW50 intraday deviation reversion research and outlines the next research directions.

The current result should be interpreted as a refined signal research workflow, not as a production-ready trading strategy.

---

## 1. Current Research Positioning

The current strongest version is v2-B3.

v2-B3 should be described as:

```text
final signal candidate
```

not as:

```text
final tradable strategy
```

This distinction is important.

The research has shown that the signal layer can be improved through market-logic filters, event-level validation, cost stress testing, and high-risk sample review. However, live execution feasibility has not yet been proven.

---

## 2. Known Limitations

### 2.1 No Tick-Level Order Book Data

The current research does not use tick-level order book data.

Missing information includes:

* bid price
* ask price
* spread
* queue position
* order book depth
* limit order fill probability
* real intraday liquidity condition

This is important because the strategy has a thin average edge. Without order book data, execution quality cannot be fully evaluated.

---

### 2.2 No Real Fill-Rate Study

The research does not yet verify whether the strategy can realistically enter and exit at the assumed prices.

Important unanswered questions:

```text
Can the strategy enter with limit orders?
How often would the order be filled?
Would chasing the price destroy the edge?
How much adverse selection exists after entry?
```

A signal can look good in backtest but fail in live trading if it cannot be executed efficiently.

---

### 2.3 Cost and Slippage Sensitivity

v2-B3 performs well before heavy cost assumptions, but the strategy becomes much weaker after transaction cost and slippage stress.

Main interpretation:

```text
The signal layer is meaningful.
The execution layer remains unproven.
```

This is one of the most important limitations.

Because the average PnL per trade is thin, even small execution friction can materially change the result.

---

### 2.4 Limited Sample Size

The event dataset contains hundreds of trade events, which is useful for exploratory research but still limited for robust machine learning validation.

This affects:

* model stability
* feature importance reliability
* validation AUC
* regime generalization
* confidence in rare subgroups

The sample is enough to support research direction, but not enough to claim a robust AI trading system.

---

### 2.5 Regime Dependence

The signal quality varies across time periods.

Different years and market environments may have different:

* liquidity conditions
* intraday volatility
* ETF tracking behavior
* investor behavior
* spread and execution quality
* market microstructure conditions

Therefore, the strategy requires further walk-forward validation before stronger conclusions can be made.

---

### 2.6 AI Model Is Not Tradable by Itself

The AI-assisted validation layer does not produce a standalone trading model.

Main reasons:

* validation AUC is weak
* XGBoost overfits
* Random Forest is more useful for feature importance than prediction
* the sample size is limited
* live execution data is missing
* transaction cost dominates many borderline signals

The AI module should be used for:

```text
feature validation
signal ranking
sample review
future research direction
```

not for:

```text
direct automated trading
```

---

### 2.7 No Live Paper Trading Yet

The research does not include live paper trading.

A future live paper-trading test would help evaluate:

* real-time signal generation
* order placement feasibility
* execution delay
* bid-ask spread impact
* fill probability
* intraday operational constraints

This is necessary before any live deployment discussion.

---

## 3. Why Not Keep Adding More Filters?

At the current stage, adding more entry filters may increase the risk of overfitting.

The strategy already went through several logical refinements:

```text
v1.1 baseline
→ TW50 upward confirmation
→ deviation slope filter
→ weak session exclusion
→ cost stress test
→ high-risk sample review
→ AI-assisted validation
```

The next bottleneck is not simply signal filtering.

The next bottleneck is:

```text
execution feasibility
cost robustness
exit efficiency
repeated-signal decay control
```

Therefore, future work should focus on execution-aware research rather than endlessly creating v2-C, v2-D, and v2-E.

---

## 4. Future Work Direction 1: Lunch-Tail Execution-Aware Filter

### Problem

The high-risk review found that the 12:45–13:00 lunch-tail period becomes weaker after cost.

Potential reason:

```text
less time remaining before market close
weaker reversion window
higher execution sensitivity
thin remaining edge
```

### Research Question

Should lunch-tail signals require stronger confirmation?

Possible stricter conditions:

* stronger TW50 return
* deeper entry deviation
* better volume ratio
* lower execution cost estimate
* earlier exit rule
* stronger expected edge threshold

### Goal

The goal is not to blindly remove all lunch-tail signals.

The goal is to test whether lunch-tail trades should only be accepted when the expected edge is strong enough to compensate for shorter remaining time and higher execution sensitivity.

---

## 5. Future Work Direction 2: Repeated Signal Expected-Edge Threshold

### Problem

Repeated signals in the same day show signs of signal decay, especially from the third signal onward.

Possible interpretation:

```text
first signal captures the cleanest deviation
second signal may still have some edge
third or later signals may reflect noise, crowding, or unstable intraday behavior
```

### Research Question

Should later same-day signals require higher expected edge?

Possible rules to test:

```text
if signal_count_today >= 3:
    require deeper deviation
    or stronger TW50 momentum
    or better volume confirmation
    or lower cost estimate
```

### Goal

The goal is to reduce low-quality repeated signals without removing all same-day opportunities.

This can help distinguish:

```text
fresh deviation opportunity
vs.
repeated noisy signal after the main opportunity has already been consumed
```

---

## 6. Future Work Direction 3: EXIT_TIME Exit-Efficiency Research

### Problem

EXIT_TIME samples are not necessarily toxic, but they indicate that the current exit rule may be inefficient.

Some trades may have partial reversion before the time exit, but fail to capture enough edge before cost.

### Research Question

Can the exit rule be improved?

Possible exit variations:

* earlier time stop
* partial reversion exit
* dynamic exit based on deviation repair
* exit when TW50 momentum weakens
* exit when ETF catches up partially
* volatility-adjusted time stop

### Goal

The goal is to reduce holding time risk and improve after-cost performance.

This direction is especially important because thin-edge strategies often lose performance through inefficient exits rather than bad entries alone.

---

## 7. Future Work Direction 4: Execution Feasibility Review

Although not part of the current final strategy version, execution feasibility is the most important next research layer.

Potential checks:

```text
spread proxy
volume at entry
time-to-close
intraday liquidity
bar-level adverse movement
fill probability assumption
limit order vs market order comparison
```

Main questions:

```text
Can the edge survive realistic fill assumptions?
Can entries be made without crossing the spread?
How often does execution cost consume the expected edge?
Which sessions are most execution-sensitive?
```

This research would help determine whether the signal candidate can move closer to a tradable strategy.

---

## 8. Future Work Direction 5: Walk-Forward Validation

The current research uses time-based splits, but a more robust next step would be walk-forward validation.

Potential structure:

```text
train on earlier period
validate on next period
roll forward
repeat
```

Purpose:

* test regime stability
* reduce overfitting risk
* observe feature importance drift
* check whether filters remain useful across time
* evaluate signal decay over market regimes

Walk-forward validation is especially important for strategies that depend on intraday microstructure and ETF tracking behavior.

---

## 9. Future Work Direction 6: AI Signal Ranking

The current AI module should not be used for direct trading.

However, it may be useful as a signal ranking tool.

Potential use:

```text
rank signals by estimated quality
review highest-score and lowest-score samples
compare model score buckets
identify weak clusters
support future filtering research
```

This avoids overclaiming AI prediction power while still using machine learning to improve research efficiency.

---

## 10. Recommended Research Priority

The next research priority should be:

```text
1. Execution feasibility
2. EXIT_TIME exit-efficiency review
3. Repeated-signal threshold
4. Lunch-tail condition tightening
5. Walk-forward validation
6. AI signal ranking refinement
```

The highest priority is execution feasibility because the current strategy is cost-sensitive.

---

## 11. What Should Not Be Claimed

This project should not claim:

```text
production-ready strategy
live arbitrage system
AI trading model
guaranteed profitability
fully validated execution edge
```

The correct claim is:

```text
This project demonstrates a disciplined research workflow for refining an intraday ETF deviation signal candidate and evaluating its limitations through event-level analysis, cost stress testing, high-risk sample review, and AI-assisted feature validation.
```

---

## 12. Summary

The project has enough evidence to support a research portfolio narrative:

```text
The signal has conditional value.
TW50 direction improves signal quality.
Deviation slope helps avoid late entry.
Session timing matters.
Execution cost is the main bottleneck.
AI supports feature validation, not direct trading.
```

The next stage should focus on turning the refined signal candidate into an execution-aware research framework.

This means moving from:

```text
Can the signal work in backtest?
```

to:

```text
Can the signal survive realistic execution constraints?
```
