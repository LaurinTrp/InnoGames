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
HEADERS = {"User-Agent": "brewery-notebook/1.0"}
engine = create_engine("sqlite:///brewery.sql")

def extract(params, BASE=BASE, delay=0.3, per_page=200):
    frames, page = [], 1
    while True:
        r = requests.get(
            BASE,
            params={**params, "per_page": per_page, "page": page},
            headers=HEADERS,
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

def filter_data(df):
    try:
        df = extract({})
    except requests.exceptions.RequestException as e:
        print("API unavailable, falling back to local sqlite:", e)
        df = pd.read_sql("SELECT * FROM brewery", con=engine)
    
    print("---------BEFORE FILTERING---------")
    print(df.info())
    
    df = df[["id", "name", "brewery_type", "state_province", "country", "city", "phone"]]
    
    print("---------AFTER FILTERING---------")
    print(df.info())
    print(df.head())

    return df

def save_local_db():
    df.to_sql(name="brewery", con=engine, if_exists="replace", index=False)

if __name__ == "__main__":
    df = extract({})
    df = filter_data(df)

brewery_data = pd.read_sql("SELECT * FROM brewery", con=engine)
print(brewery_data.info())

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

small = brewery_types["n"] / total < 0.02
other = pd.DataFrame({"brewery_type": ["other"], "n": [brewery_types.loc[small, "n"].sum()]})
grouped = pd.concat([brewery_types[~small], other], ignore_index=True)

plt.figure(figsize=(6, 6))
plt.pie(grouped["n"], labels=grouped["brewery_type"], autopct="%1.1f%%", startangle=90, pctdistance=0.8, counterclock=False)

plt.title("Brewery Types")
plt.savefig("out/brewery_types.png")
plt.show()

sql_command = '''
    SELECT state_province, country, brewery_type, COUNT(*) AS n
    FROM brewery
    WHERE country = 'United States'
      AND brewery_type = 'micro'
    GROUP BY state_province, country, brewery_type
    ORDER BY n DESC
'''

micro_breweries_per_state = pd.read_sql(sql_command, con=engine)

top = micro_breweries_per_state.iloc[0]
state = top["state_province"]
amount = top["n"]

print("The state with the most micro breweries in the US is", state, "with", amount, "micro breweries")

BASE = "https://api.openbrewerydb.org/v1/breweries/meta"
r = requests.get(
    BASE,
    params={
        "by_country": "United States", "by_type":"micro"
    },
    headers=HEADERS,
    timeout=30,
)
r.raise_for_status()
data = r.json()

df_meta = pd.DataFrame([data])

by_state = pd.Series(data["by_state"]).astype(int)

top = by_state.sort_values(ascending=False).head(1)

state = top.index[0]
amount = top.iloc[0]

print("The state with the most micro breweries in the US is", state, "with", amount, "micro breweries")

sql_command = '''
    SELECT state_province, country, COUNT(*) AS n
    FROM brewery
    WHERE country = 'United States'
    GROUP BY state_province, country
    ORDER BY n DESC
'''

breweries_per_state = pd.read_sql(sql_command, con=engine)

fig = px.choropleth(breweries_per_state,
                    locations='state_province',
                    locationmode="USA-states",
                    scope="usa",
                    color='n',
                    labels={"n": "Breweries"},
                    color_continuous_scale="Viridis_r",
                    )
fig.update_layout(title_text="Breweries per State",
                  title_font_size=22,
                  title_x=0.45,
                  width=900,
                  height=550
                  )
fig.write_image("out/breweries_per_state.png")
fig.show()

top_5_states = micro_breweries_per_state.head(5)

print("The top 5 states in the USA with the most microbreweries are:")
count = 1
for state in top_5_states["state_province"]:
    print(count, state)
    count+=1

x = top_5_states["state_province"]
y = top_5_states["n"]

plt.bar(x, y)
plt.yticks(np.arange(0, 500, 50))
plt.xlabel("US State")
plt.ylabel("Brewery amount")
plt.title("Top 5 US States for breweries")
plt.tight_layout()

plt.savefig("out/top_five_us.png")

plt.show()

sql_command = '''
    SELECT state_province, brewery_type, COUNT(*) AS n
    FROM brewery
    WHERE state_province = 'Incheon'
      AND brewery_type = 'brewpub'
'''

brewpubs_incheon = pd.read_sql(sql_command, con=engine)
brewpubs_incheon_count = brewpubs_incheon.iloc[0]["n"]

print("There are", brewpubs_incheon_count, "brewpub breweries in Incheon, South Korea")

BASE = "https://api.openbrewerydb.org/v1/breweries/meta"
r = requests.get(
    BASE,
    params={
        "by_country": "South Korea", "by_state": "Incheon", "by_type":"brewpub"
    },
    headers=HEADERS,
    timeout=30,
)
r.raise_for_status()
data = r.json()

brewpubs_incheon_count = data["total"]

print("There are", brewpubs_incheon_count, "brewpub breweries in Incheon, South Korea")

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
