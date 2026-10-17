import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
from sqlalchemy import create_engine
import plotly.express as px
import os

os.makedirs("out", exist_ok=True)

BASE = "https://api.openbrewerydb.org/v1/breweries"
engine = create_engine("sqlite:///brewery.sql")

# Fetch data from API
def extract(params, BASE=BASE, delay=0.3, per_page=200):
    frames, page = [], 1
    while True:
        r = requests.get(
            BASE,
            params={**params, "per_page": per_page, "page": page},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        frames.append(pd.DataFrame(data))
        page += 1
        time.sleep(delay)
    return pd.concat(frames, ignore_index=True)

# Filter data for relevant data
def filter_data(df):
    print("---------BEFORE FILTERING---------")
    print(df.info())

    df = df[["id", "name", "brewery_type", "state_province", "country", "city", "phone"]]

    print("---------AFTER FILTERING---------")
    print(df.info())
    print(df.head())

    return df

# Save data to sqlite file
def save_local_db(df):
    df.to_sql(name="brewery", con=engine, if_exists="replace", index=False)

def answer_questions():
    print("Answer to question 1:")
    # Fetch microbreweries per us state descending with limit 5
    sql_command = '''
        SELECT state_province, country, brewery_type, COUNT(*) AS n
        FROM brewery
        WHERE country = 'United States'
        AND brewery_type = 'micro'
        GROUP BY state_province, country, brewery_type
        ORDER BY n DESC
        LIMIT 5
    '''

    top_states_by_micro_breweries = pd.read_sql(sql_command, con=engine)

    # Get the state with the most microbreweries
    top = top_states_by_micro_breweries.iloc[0]
    state = top["state_province"]
    amount = top["n"]

    print("The state with the most micro breweries in the US is", state, "with", amount, "micro breweries")

    print("Answer to question 2:")

    # Reusing the top_states_by_micro_breweries
    print("The top 5 states in the USA with the most microbreweries are:")
    count = 1
    for state in top_states_by_micro_breweries["state_province"]:
        print(count, state)
        count += 1

    print("Answer to question 3:")
    # Fetching the brewpubs based in Incheon from the DB
    sql_command = '''
        SELECT state_province, brewery_type, COUNT(*) AS n
        FROM brewery
        WHERE state_province = 'Incheon'
        AND brewery_type = 'brewpub'
    '''

    brewpubs_incheon = pd.read_sql(sql_command, con=engine)
    brewpubs_incheon_count = brewpubs_incheon.iloc[0]["n"]

    print("There are", brewpubs_incheon_count, "brewpub breweries in Incheon, South Korea")

    print("Answer to question 4:")
    # Fetching the phone numbers in korean citys to check for common prefixes
    # Only using the citys where at least two numbers are entered because otherwise no pattern can be found
    sql_command = '''
        SELECT country, city, phone
        FROM brewery
        WHERE country = 'South Korea'
        AND phone IS NOT NULL
    '''

    phones_korea = pd.read_sql(sql_command, con=engine)

    numbers_by_city = phones_korea.groupby("city")["phone"].apply(list)

    for city, phones in numbers_by_city.items():
        if len(phones) < 2:
            continue
        print(city, "\t", os.path.commonprefix(phones))


def visualize():
    # Visualize the different brewery types as a pie chart
    sql_command = '''
        SELECT brewery_type, COUNT(*) as n
        FROM brewery
        GROUP BY brewery_type
    '''
    
    brewery_types = pd.read_sql(sql_command, con=engine)
    brewery_types = brewery_types.sort_values("n", ascending=False)
    
    types = brewery_types["brewery_type"]
    amounts = brewery_types["n"]
    total = amounts.sum()
    
    # Combine less represented types for the chart
    small = brewery_types["n"] / total < 0.02
    other = pd.DataFrame({"brewery_type": ["other"], "n": [brewery_types.loc[small, "n"].sum()]})
    grouped = pd.concat([brewery_types[~small], other], ignore_index=True)
    
    plt.figure(figsize=(6, 6))
    plt.pie(grouped["n"], labels=grouped["brewery_type"], autopct="%1.1f%%", startangle=90, pctdistance=0.8, counterclock=False)
    
    plt.title("Brewery Types")
    plt.savefig("out/brewery_types.png")
    plt.close()
    

    # Visualize the distribution of breweries per state as a heatmap of the USA
    sql_command = '''
        SELECT state_province, country, COUNT(*) AS n
        FROM brewery
        WHERE country = 'United States'
        GROUP BY state_province, country
        ORDER BY n DESC
    '''
    breweries_per_state = pd.read_sql(sql_command, con=engine)

    fig = px.choropleth(
        breweries_per_state,
        locations="state_province",
        locationmode="USA-states",
        scope="usa",
        color="n",
        labels={"n": "Breweries"},
        color_continuous_scale="Viridis_r",
    )
    fig.update_layout(
        title_text="Breweries per State",
        title_font_size=22,
        title_x=0.45,
        width=900,
        height=550,
    )
    fig.write_image("out/breweries_per_state.png")
    fig.show()

    
    # Visualize these 5 states as a bar diagram with the amount of microbreweries they have
    sql_command = '''
        SELECT state_province, country, brewery_type, COUNT(*) AS n
        FROM brewery
        WHERE country = 'United States'
        AND brewery_type = 'micro'
        GROUP BY state_province, country, brewery_type
        ORDER BY n DESC
    '''
    top_5_states = pd.read_sql(sql_command, con=engine).head(5)

    plt.bar(top_5_states["state_province"], top_5_states["n"])
    plt.yticks(np.arange(0, 500, 50))
    plt.xlabel("US State")
    plt.ylabel("Brewery amount")
    plt.title("Top 5 US States for microbreweries")
    plt.tight_layout()
    plt.savefig("out/top_five_us.png")
    plt.close()


if __name__ == "__main__":
    print("Extracting data...")
    df = extract({})
    print("Data extracted successfully")

    print("Filtering data...")
    df = filter_data(df)
    print("Data filtered successfully")

    print("Saving data to local database...")
    save_local_db(df)
    print("Data saved successfully")

    print("Answering questions...")
    answer_questions()
    print("Questions answered successfully")

    print("Creating visualizations...")
    visualize()
    print("Visualizations created successfully")
