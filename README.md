# Supply Chain Delivery & Profit Analysis

An end-to-end analytics project on a distributor's order data: SQL modelling, data-quality checks, and (in progress) a Power BI dashboard and a late-delivery prediction model.

## The business question

**Where is this company losing money and customer trust, and what would fix it?**

I looked at two problems: deliveries that miss their promised dates, and order lines that lose money.

## Key findings

| Finding | Evidence |
|---|---|
| **First Class shipping is late on every delivery.** It promises 1 day and consistently takes 2. | 100% late across 26,513 delivered order lines |
| Promises are the problem, not speed. Standard Class promises 4 days and is late far less often. | Standard Class 39.8% late, Second Class 79.8%, Same Day 47.9% |
| **Geography does not explain lateness.** | Late rate is 56.8%-57.7% in all five markets |
| **Roughly 1 in 5 order lines loses money**, in every department. | 17.7%-23.5% of lines are loss-making by department |
| **Discounts don't explain the losses.** | 18.4% of lines lose money with no discount vs 19.0% at 20%+ |
| Losses come from individual lines, not bad products. | Almost every product is net profitable overall |

**Recommendation:** review the delivery promise for First Class (and Second Class). Reset the promised time to match what the operation actually delivers, or fix the process behind it. Then investigate why about 18-19% of lines lose money, since discounting and geography are not the cause.

## Data

- **Source:** DataCo Smart Supply Chain for Big Data Analysis (available on Kaggle and Mendeley Data). The raw file is **not** stored in this repo; download it and place `DataCoSupplyChainDataset.csv` in `data/`.
- **Size:** 180,519 order lines across 65,752 orders, 20,652 customers and 118 products, January 2015 to January 2018.
- These findings describe this dataset only. They are not claims about real-world supply chains.

### Data-quality decisions

- **Removed personal data** (emails, names, passwords, street addresses). It isn't needed and shouldn't be in a portfolio repo.
- **Dropped** a fully empty column, a mostly empty zip code column, an image URL column, and three duplicated columns.
- **Cancelled shipments are excluded from delivery metrics**, because a cancelled shipment can't be on time or late.
- **Product categories are unreliable.** Each product has one category in the source data, but the pairings don't make sense (for example, a "Perfect Rip Deck" under Cleats). I used departments and avoided conclusions based on category names.
- **The data changes shape from late 2017.** Orders up to September 2017 average about three items each; from October 2017 each order has one item. The apparent sales collapse after that point looks like a data artifact, not a real downturn, so trend analysis should be read with this in mind.

## Data model

A star schema with one row per order line item in the fact table:

```
                dim_customer
                     |
dim_product --- fact_order_item --- dim_location
                     |
                  dim_date
```

## Repository structure

```
data/         raw and processed data (not tracked in Git)
notebooks/    01_clean_and_model.py   clean the raw file and build the star schema
sql/          01_schema.sql           PostgreSQL table definitions
              02_analysis.sql         six business-question queries
scripts/      02_load_to_supabase.py  load the tables into PostgreSQL (Supabase)
              03_run_analysis.py      run the SQL locally with DuckDB
reports/      CSV outputs of each query
```

## How to run it

```bash
pip install pandas duckdb psycopg2-binary
python notebooks/01_clean_and_model.py     # builds data/processed/*.csv
python scripts/03_run_analysis.py          # runs the SQL, writes reports/*.csv
```

The SQL queries use CTEs, joins, and window functions (moving averages, `LAG`, `RANK`) and run on both DuckDB and PostgreSQL.

## Tech stack

Python (pandas), SQL (PostgreSQL / DuckDB), Supabase, Power BI, Git and GitHub.

## Status

- [x] Data cleaning and star-schema modelling
- [x] SQL analysis (six business questions)
- [ ] Power BI dashboard (in progress)
- [ ] Late-delivery prediction model
- [ ] Load into Supabase and connect Power BI to it

## Author

Built by Sinazo. GitHub: [Sinazo-Mighty](https://github.com/Sinazo-Mighty)
