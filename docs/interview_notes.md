# Interview Notes

This document summarizes likely interview questions and concise answers for the 0050 vs TW50 intraday deviation reversion research project.

The goal is to communicate the research clearly, conservatively, and professionally.

---

## 1. What is this project about?

This project studies an intraday deviation reversion signal between Taiwan 0050 ETF and a TW50 simulated NAV reference.

The main idea is that when 0050 trades below its simulated NAV, the negative deviation may sometimes represent a temporary tracking lag. However, not every negative deviation is tradable, so the research focuses on identifying the conditions under which the signal quality improves.

The project is not presented as a production-ready trading system. It is a research portfolio showing a complete workflow from market hypothesis to event dataset, strategy iteration, cost stress testing, high-risk sample review, and AI-assisted validation.

---

## 2. Why compare 0050 with TW50?

0050 is an ETF tracking Taiwan 50 exposure, while TW50 simulated NAV can be used as a reference for the underlying basket movement.

The research assumption is that short-term mismatch between ETF price and the reference basket may create temporary intraday deviation.

However, this mismatch only matters if it behaves like a tracking lag rather than broader market repricing. That is why the strategy does not use deviation alone.

---

## 3. Why is TW50_return_5m important?

TW50_return_5m is used as a short-term confirmation of the underlying reference direction.

If TW50 is moving upward while 0050 still shows negative deviation, the setup is more likely to represent ETF price lagging the underlying reference.

In contrast, if TW50 is weak or non-confirming, a negative deviation may simply reflect risk repricing or weak market condition.

Therefore, TW50_return_5m helps distinguish:

```text id="mrjsnc"
tracking lag
vs.
risk repricing
```

---

## 4. What changed from v1.1 to v2-A?

v1.1 was the baseline version, with 361 trades and PF about 1.98.

v2-A added:

```text id="82hm0c"
TW50_return_5m > 0
```

After this filter:

```text id="ntydcs"
trades decreased from 361 to 258
PF improved from about 1.98 to about 2.66
gross loss decreased
max single loss improved
```

The interpretation is not simply that fewer trades improved performance. The TW50 filter added market confirmation and improved signal quality.

---

## 5. Why exclude positive deviation slope?

Positive deviation slope may indicate that the deviation has already started repairing before entry.

If the strategy enters after part of the reversion has already happened, the remaining expected edge may be smaller and more vulnerable to cost.

So excluding positive slope is a way to reduce late-entry signals.

The logic is:

```text id="45vxi1"
do not enter after the cleanest part of the reversion has already started
```

---

## 6. Why exclude the 09:45–10:00 window?

The 09:45–10:00 window appeared weaker in the failure analysis.

One possible interpretation is that after the initial opening reaction, the clean early dislocation may have already been partially repaired, while remaining signals become more mixed.

Therefore, excluding this weak window helps reduce lower-quality samples.

This is not treated as a universal rule for all markets. It is a finding specific to this dataset and should be further validated with more data.

---

## 7. What is v2-B3?

v2-B3 is the current final signal candidate.

It combines:

```text id="me6g4o"
TW50_return_5m > 0
exclude deviation_slope_1bar > 0
exclude the main 09:45–10:00 weak window
```

Main result:

```text id="kb5vee"
223 trades
Net PnL about 7.80
Avg PnL about 0.035
PF about 3.60
Gross Loss about -3.00
Max Loss about -0.25
```

But v2-B3 is not a final tradable strategy. It is a refined signal layer that still requires execution feasibility research.

---

## 8. Why not call v2-B3 a tradable strategy?

Because execution feasibility has not been proven.

The strategy is thin-edge. Average PnL per trade is small, so transaction cost and slippage can materially affect performance.

The research does not yet include:

```text id="o73mda"
tick-level order book
real bid-ask spread
limit order fill probability
queue position
live paper trading
real execution records
```

Therefore, it is more accurate to call v2-B3 a final signal candidate, not a live-ready strategy.

---

## 9. What did the cost stress test show?

The cost stress test showed that execution is the main bottleneck.

v2-B3 performs well before heavy cost assumptions, but:

```text id="btfzbs"
Cost 0.01 is still relatively acceptable
Cost 0.02 weakens the edge significantly
0.5 tick each side slippage can make the strategy fail
```

This means that the next stage should focus on execution quality rather than only adding more signal filters.

---

## 10. Why is high realized volatility not directly excluded?

High realized volatility is often treated as risk, but the high-risk review showed that under the v2-B3 condition set, high RV samples contributed positively.

This suggests that high RV may sometimes represent larger intraday dislocation and larger reversion opportunity.

So high RV should not be blindly removed. It should be studied conditionally.

The key question is:

```text id="8zv7l3"
Is volatility pure noise, or does it create larger temporary deviation under the right conditions?
```

---

## 11. What did the high-risk sample review find?

The high-risk review found several important remaining risk areas:

```text id="x7vgdx"
Lunch tail 12:45–13:00 becomes weaker after cost
Repeated signals show signal decay, especially from the third signal onward
EXIT_TIME samples are not toxic but indicate weaker exit efficiency
High RV should not be blindly excluded
Some earlier-period samples are more cost fragile
```

These findings help define future work directions.

---

## 12. What is the AI validation module doing?

The AI module converts the v1.1 event dataset into a supervised learning sample.

The target label is:

```text id="p11a4a"
good_signal_cost002 = 1 if pnl_twd - 0.02 > 0
```

This means a trade is considered a good signal only if it remains profitable after a 0.02 round-trip cost assumption.

The models are used to check whether entry-time features can explain signal quality.

It is AI-assisted validation, not AI trading.

---

## 13. Why not use the AI model directly for trading?

Because the model is not strong enough out-of-sample.

Main issues:

```text id="7h9z19"
sample size is limited
validation AUC is weak
XGBoost overfits
Random Forest is more useful for feature importance than prediction
market regimes change
execution cost dominates many thin-edge trades
```

Therefore, the AI model is used as a research tool, not a trading engine.

---

## 14. What features did AI validation support?

The feature importance results supported several dimensions already found in the rule-based research:

```text id="e9ceor"
deviation slope
TW50 returns
realized volatility
entry timing
volume ratio
entry relative deviation
signal count
```

This does not prove that the AI model can trade. But it does support the idea that the rule-based research focused on relevant signal-quality features.

---

## 15. What is the main value of this project?

The main value is the complete research process.

It demonstrates:

```text id="a4ionv"
market hypothesis construction
event dataset design
conditional signal testing
failure analysis
strategy refinement
cost and slippage awareness
high-risk sample taxonomy
AI-assisted feature validation
conservative communication
```

The strongest point is not simply a high PF. The stronger point is showing how a market idea can be translated into a disciplined research workflow.

---

## 16. What would you do next?

The next stage should focus on execution feasibility and exit efficiency.

Priority future work:

```text id="0pdvw6"
1. Execution feasibility review
2. EXIT_TIME exit-efficiency research
3. Repeated signal expected-edge threshold
4. Lunch-tail execution-aware filter
5. Walk-forward validation
6. AI signal ranking refinement
```

The most important next question is:

```text id="85owul"
Can the refined signal candidate survive realistic execution constraints?
```

---

## 17. How would you explain this project in one minute?

This project studies whether 0050 ETF intraday negative deviation relative to a TW50 simulated NAV reference can behave like a short-term reversion signal.

I first built a v1.1 baseline and converted trades into an event dataset. Then I tested whether TW50 short-term direction improves signal quality. Adding TW50_return_5m > 0 reduced trades from 361 to 258 and improved PF from about 1.98 to about 2.66.

After failure analysis, I refined the signal into v2-B3 by excluding late-entry slope cases and the main 09:45–10:00 weak window. v2-B3 reached 223 trades and PF about 3.60, but I treat it only as a final signal candidate because cost and slippage sensitivity remain high.

Finally, I added AI-assisted validation by labeling cost-adjusted good signals and testing feature importance. The AI model is not used for direct trading, but it supports the importance of features like TW50 returns, deviation slope, realized volatility, timing, and volume ratio.

The main value of the project is the disciplined research workflow, not a claim of live-ready profitability.

---

## 18. Short Answer to “Is this overfitting?”

There is always overfitting risk in strategy research.

I tried to reduce it by:

```text id="7oz4j6"
using market logic before adding filters
building event-level datasets
doing failure analysis instead of random parameter search
checking cost and slippage sensitivity
separating train / validation / recent periods
not claiming v2-B3 is production-ready
using AI only for feature validation
```

The current result is best interpreted as a refined signal candidate that needs execution research and further walk-forward validation.

---

## 19. Short Answer to “Why should this matter to a quant team?”

Because the project shows a full research loop:

```text id="uai4he"
observe market structure
form hypothesis
construct event dataset
test conditions
analyze failures
refine signal
stress-test cost
classify high-risk samples
validate features with AI
communicate limitations clearly
```

This is closer to an internal research workflow than simply showing a backtest chart.

---

## 20. Final Positioning Statement

This project should be described as:

```text id="4tel9a"
A research portfolio demonstrating a disciplined workflow for developing and validating an intraday ETF deviation signal candidate.
```

It should not be described as:

```text id="52wtps"
A finished live arbitrage strategy.
```
