import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Linked Views", layout="wide")

CATEGORIES = ['Appliances', 'Furniture', 'Clothing', 'Games', 'Phones']
# Approximate country centres so the map is geographically meaningful
COUNTRY_CENTRES = {
    'Malaysia': (4.2, 102.0), 'Singapore': (1.35, 103.8), 'Indonesia': (-2.5, 118.0),
    'Thailand': (15.0, 101.0), 'Brunei': (4.5, 114.7),
}
COUNTRY_SPREAD = {'Malaysia': 2.0, 'Singapore': 0.1, 'Indonesia': 4.0, 'Thailand': 2.5, 'Brunei': 0.3}
WORLD_URL = "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json"


@st.cache_data
def make_data(n: int = 200) -> pd.DataFrame:
    # Fixed seed so the app does not reshuffle on every Streamlit rerun
    rng = np.random.default_rng(42)
    country = rng.choice(list(COUNTRY_CENTRES), size=n)
    lat = [COUNTRY_CENTRES[c][0] + rng.normal(0, COUNTRY_SPREAD[c]) for c in country]
    lon = [COUNTRY_CENTRES[c][1] + rng.normal(0, COUNTRY_SPREAD[c]) for c in country]
    df = pd.DataFrame({
        'Product Category': rng.choice(CATEGORIES, size=n),
        'Sales': rng.integers(50, 500, size=n),
        'Price': rng.integers(5, 100, size=n),
        'Quantity': rng.integers(1, 20, size=n),
        'Country': country,
        'Latitude': lat,
        'Longitude': lon,
    })
    return df.reset_index().rename(columns={'index': 'Index'})


data = make_data()
cat_color = alt.Color('Product Category:N', scale=alt.Scale(domain=CATEGORIES))

st.title("Linked Views: Data Visualization Examples")
example = st.sidebar.selectbox("Choose an Example", ["Bar + Scatter", "Line + Histogram", "Pie + Bar", "Map + Scatter"])
st.sidebar.caption("Click, shift-click or brush on the top chart: the other chart updates. Click empty space to clear.")

if example == "Bar + Scatter":
    st.subheader("Bar Chart + Scatter Plot")
    st.caption("Click one or more bars (shift-click for several) to filter the scatter plot.")
    pick = alt.selection_point(fields=['Product Category'])

    bar = alt.Chart(data).mark_bar().encode(
        x='Product Category:N', y='sum(Sales):Q', color=cat_color,
        opacity=alt.condition(pick, alt.value(1), alt.value(0.3)),
        tooltip=['Product Category', 'sum(Sales)'],
    ).add_params(pick).properties(height=300)

    scatter = alt.Chart(data).mark_circle(size=60).encode(
        x='Price:Q', y='Quantity:Q', color=cat_color,
        tooltip=['Product Category', 'Price', 'Quantity'],
    ).transform_filter(pick).properties(height=300)

    st.altair_chart(alt.vconcat(bar, scatter), use_container_width=True)

elif example == "Line + Histogram":
    st.subheader("Line Chart + Histogram")
    st.caption("Drag across the line chart to brush a range of records; the histogram shows only the brushed range.")
    brush = alt.selection_interval(encodings=['x'])

    line = alt.Chart(data).mark_line(point=True).encode(
        x='Index:Q', y='Price:Q', color=cat_color,
        tooltip=['Index', 'Product Category', 'Price'],
    ).add_params(brush).properties(height=280)

    hist = alt.Chart(data).mark_bar().encode(
        x=alt.X('Quantity:Q', bin=alt.Bin(maxbins=10)), y='count():Q', color=cat_color,
    ).transform_filter(brush).properties(height=280)

    st.altair_chart(alt.vconcat(line, hist), use_container_width=True)

elif example == "Pie + Bar":
    st.subheader("Pie Chart + Bar Chart")
    st.caption("Click a pie slice to see that category's sales by country.")
    pick = alt.selection_point(fields=['Product Category'])

    pie = alt.Chart(data).mark_arc(outerRadius=130).encode(
        theta='sum(Sales):Q', color=cat_color,
        opacity=alt.condition(pick, alt.value(1), alt.value(0.3)),
        tooltip=['Product Category', 'sum(Sales)'],
    ).add_params(pick).properties(height=300)

    bars = alt.Chart(data).mark_bar().encode(
        x='Country:N', y='sum(Sales):Q', color=alt.Color('Country:N'),
        tooltip=['Country', 'sum(Sales)'],
    ).transform_filter(pick).properties(height=300)

    # Concat charts share the colour scale by default; the pie's scale is pinned to the
    # product categories, so country bars would get no colour. Keep the scales separate.
    st.altair_chart(alt.hconcat(pie, bars).resolve_scale(color='independent'), use_container_width=True)

elif example == "Map + Scatter":
    st.subheader("Map View + Scatter Plot")
    st.caption("Click points on the map (shift-click for several) to select a country; the scatter shows only those sales.")
    pick = alt.selection_point(fields=['Country'])

    base = alt.Chart(alt.topo_feature(WORLD_URL, 'countries')).mark_geoshape(
        fill='#e8e8e8', stroke='white'
    ).project('mercator', scale=650, center=[110, 5]).properties(width=600, height=360)

    points = alt.Chart(data).mark_circle(size=60).encode(
        longitude='Longitude:Q', latitude='Latitude:Q', color=cat_color,
        opacity=alt.condition(pick, alt.value(0.9), alt.value(0.15)),
        tooltip=['Country', 'Product Category', 'Sales'],
    ).add_params(pick).project('mercator', scale=650, center=[110, 5])

    scatter = alt.Chart(data).mark_circle(size=60).encode(
        x='Sales:Q', y='Quantity:Q', color=cat_color,
        tooltip=['Country', 'Product Category', 'Sales', 'Quantity'],
    ).transform_filter(pick).properties(width=380, height=360)

    st.altair_chart(alt.hconcat(base + points, scatter), use_container_width=True)
