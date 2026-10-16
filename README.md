# End-to-End Brewery Data Pipeline

ETL pipeline and analysis for **Case A** of the [Basic End-to-End Pipeline Design](./End-to-End%20Pipeline%20Design.pdf) task: fetch brewery data from the [Open Brewery DB API](https://www.openbrewerydb.org/), load it into a local SQLite database, answer analytical questions, and produce visualizations.

The full implementation lives in [`End-To-End-Pipeline.ipynb`](./End-To-End-Pipeline.ipynb).

## Pipeline

| Stage         | What happens                                                                                                                                             |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Extract**   | Paginated `GET` requests to `https://api.openbrewerydb.org/v1/breweries` (200 records per page). Falls back to a local SQLite if the API is unavailable. |
| **Transform** | Keep relevant columns: `id`, `name`, `brewery_type`, `state_province`, `country`, `city`, `phone`.                                                       |
| **Load**      | Write the cleaned table into SQLite (`brewery.sql`, table `brewery`).                                                                                    |

Analysis and charts are run against the database with SQL + pandas, not against raw API dumps. Some answers are cross-checked with the API `/meta` endpoint.

## Answers

| #   | Question                                       | Result                                                                                                                                     |
| --- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Which US state has the most microbreweries?    | **California** (466)                                                                                                                       |
| 2   | Top 5 US states by microbreweries?             | California, Washington, Colorado, New York, Texas                                                                                          |
| 3   | How many brewpubs in Incheon, South Korea?     | **2**                                                                                                                                      |
| 4   | (Bonus) Phone number patterns by city in Korea | Shared prefixes per city (e.g. Andong-si → `054-`, Gangneung-si → `033-`, Seogwipo-si → `064-`), matching Korean area-code style numbering |

Counts reflect a full API pull (~11,959 breweries at run time) and may change if the upstream data changes.

## Visualizations

Three charts are generated from aggregated SQL results and saved under `out/`:

1. **Pie chart** — brewery type distribution (`out/brewery_types.png`)
2. **Choropleth map** — breweries per US state (`out/breweries_per_state.png`)
3. **Bar chart** — top 5 US states by microbrewery count (`out/top_five_us.png`)

## How to run

1. Install [Jupyter](https://jupyter.org/) and open the notebook, or use VS Code / Cursor’s notebook runner.

2. Run all cells top to bottom. The first code cell installs dependencies:

   ```text
   requests, pandas, matplotlib, numpy, sqlalchemy, plotly, kaleido
   ```

3. Outputs (SQL DB + PNGs) are written to the project root and `out/`.

No external database server is required; SQLite is created locally as `brewery.sql`.

## Project layout

```text
.
├── End-to-End Pipeline Design.pdf   # Task brief
├── End-To-End-Pipeline.ipynb        # ETL + analysis + plots
├── brewery.sql                      # SQLite DB produced by the pipeline
├── out/                             # Exported visualizations
└── README.md
```

## Tech stack

Python · pandas · requests · SQLAlchemy / SQLite · matplotlib · Plotly
