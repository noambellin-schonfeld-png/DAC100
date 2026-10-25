# NETL Case 0B reproduction and reconciliation

This note records the DAC100 baseline calculation from J. Valentine and A. Zoelle, *Direct Air Capture Case Studies: Sorbent System*, DOE/NETL-2021/2865 (2022). Results are modeled estimates in the NETL study boundary; they are not plant measurements or a full lifecycle assessment.

## Source map

- Exhibit 5-16: printed p. 50, PDF viewer p. 62 (reported COC results and denominator definitions).
- Section 3.6: printed pp. 20–21, viewer pp. 32–33 (COC equation, FCR, cost year, and capacity-factor convention).
- Exhibit 3-7: printed p. 20, viewer p. 32 (Midwest transport and saline-storage assumption of $10/t in 2018 USD).
- Exhibit 5-4: printed p. 32, viewer p. 44 (gross DAC, residual NGCC emissions, net flow, and NGCC product flow).
- Exhibit 5-7: printed pp. 33–34, viewer pp. 45–46 (emissions cross-check; its rounded residual CO2 is one tonne/year higher than Exhibit 5-4).
- Exhibit 5-13: printed p. 46, viewer p. 58 (TASC).
- Exhibit 5-14: printed p. 47, viewer p. 59 (annual fixed and variable O&M and fuel costs; case capacity factor is 85%).

## Flows and denominators

At the reported 85% capacity factor, Exhibit 5-4 gives 113,900 tCO2/y gross DAC capture and 13,900 tCO2/y residual NGCC stack emissions. NETL therefore reports 100,000 tCO2/y net removal within its plant accounting boundary. This is a modeled plant balance, not lifecycle net removal. Exhibit 5-16 uses three separate annual denominators:

| Exhibit 5-16 basis | Annual denominator | Meaning |
|---|---:|---|
| DACnet | 100,000 t/y | NETL-boundary net atmospheric removal |
| DACgross | 113,900 t/y | Gross CO2 captured from air |
| Plantgross | 238,990 t/y | 113,900 DAC product + 125,090 NGCC flue-gas product sent to T&S |

These are not interchangeable. DAC100 calls $595.53/t the capture cost per gross DAC tonne (before T&S), $616.51/t the integrated cost including NETL T&S per gross DAC tonne, and $702.21/t the integrated cost per NETL-boundary net atmospheric tonne.

## Annual costs and capacity factor

The calculated annual capital charge is the printed Exhibit 5-13 TASC, $494,258,000, multiplied by the Section 3.6 FCR, 0.0707:

`$494,258,000 × 0.0707 = $34,944,040.60 per year`

Exhibit 5-14 supplies fixed O&M of $15,343,999/y, variable O&M of $6,143,693/y, and fuel of $11,399,160/y. Its header states 85% capacity factor. DAC100 takes those as reported annual costs and uses the Exhibit 5-4 annual tonnes directly. It does not multiply those annual flows or the annual variable/fuel costs by 0.85 again. Section 3.6's equation instead applies CF when its starting point is variable O&M, fuel, and CO2 flow stated at 100% CF; the factor cancels between the annualized numerator and denominator for variable costs.

For T&S, DAC100 uses $2,390,000/y from Exhibit 5-16's rounded $23.9/net-t line multiplied by 100,000 net t/y. This preserves the table's stated 2019-dollar basis. Separately, Exhibit 3-7's Midwest $10/t assumption times 238,990 t/y of combined product is $2,389,900 in 2018 USD—$100/y lower before any dollar-year conversion. The report does not show a conversion alongside the table. DAC100 follows the 2019-dollar table and flags the source-year and rounding ambiguity rather than inventing an adjustment.

Separate verification/MRV cost is not reported in this case. DAC100 enters zero only to exclude that cost from this reproduction. That does not mean verification is free. NETL also does not quantify full construction/supply-chain lifecycle emissions or storage leakage and permanence.

## Component reconciliation

DAC100 divides the above annual costs by each Exhibit 5-16 denominator. The following calculated values use printed inputs and are shown to two decimals; NETL's published table uses one decimal and rounded source inputs/outputs.

| Component | DACnet calc. / NETL | DACgross calc. / NETL | Plantgross calc. / NETL |
|---|---:|---:|---:|
| Capital | $349.44 / $349.6 | $306.80 / $307.0 | $146.22 / $146.3 |
| Fixed O&M | $153.44 / $153.4 | $134.71 / $134.7 | $64.20 / $64.2 |
| Variable O&M | $61.44 / $61.4 | $53.94 / $53.9 | $25.71 / $25.7 |
| Fuel | $113.99 / $114.0 | $100.08 / $100.1 | $47.70 / $47.7 |
| Subtotal, excl. T&S | $678.31 / $678.5 | $595.53 / $595.7 | $283.82 / $283.9 |
| CO2 T&S | $23.90 / $23.9 | $20.98 / $21.0 | $10.00 / $10.0 |
| Total, incl. T&S | $702.21 / $702.4 | $616.51 / $616.7 | $293.82 / $293.9 |

Each cell is `DAC100 calculation / NETL Exhibit 5-16`. Totals are recomputed from unrounded annual amounts; NETL's component rows and totals are independently rounded. The main visible gap is capital: the printed TASC × FCR gives $349.44/net t, versus $349.6/net t in Exhibit 5-16. The resulting totals differ by $0.08–$0.19/t across the three bases. DAC100 follows the published TASC × FCR formula rather than backing into a capital input from the rounded COC row. The T&S figure is also rounded: $23.9/net t × 100,000 net t/y gives $2,390,000/y, while $10/t × 238,990 t/y is $2,389,900 in the source's stated 2018-dollar basis. Exhibit 5-7's 13,901 t/y emissions value is one tonne higher than the 13,900 t/y in Exhibit 5-4; DAC100 follows Exhibit 5-4, the table that reconciles gross capture to NETL's 100,000 t/y net target.

## Scenario separation

The source reproduction is stored separately from the application scenarios. DAC100's maximum 30% capital, 20% fixed O&M, 25% variable O&M, and 20% fuel reductions are analyst-set exploratory bounds, not NETL sensitivity results, measured improvements, or evidence of engineering compatibility. The application holds the reported output, process-emissions balance, T&S throughput, and study boundary constant while showing conditional arithmetic. It excludes tax credits and subsidies from production cost.

The full lifecycle cost per durably removed tonne remains unquantified. A $100 target result from this model is only a comparison against NETL's narrower modeled boundary, with storage fraction as an explicit user assumption.
