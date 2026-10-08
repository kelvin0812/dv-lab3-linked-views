import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.set_page_config(page_title="Linked Views", page_icon="🔗", layout="wide")

CATEGORIES = ['Appliances', 'Furniture', 'Clothing', 'Games', 'Phones']
COUNTRIES = ['Malaysia', 'Singapore', 'Indonesia', 'Thailand', 'Brunei']
# Approximate country centres so the map is geographically meaningful
COUNTRY_CENTRES = {
    'Malaysia': (4.2, 102.0), 'Singapore': (1.35, 103.8), 'Indonesia': (-2.5, 118.0),
    'Thailand': (15.0, 101.0), 'Brunei': (4.5, 114.7),
}
COUNTRY_SPREAD = {'Malaysia': 2.0, 'Singapore': 0.1, 'Indonesia': 4.0, 'Thailand': 2.5, 'Brunei': 0.3}
WORLD_URL = "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/world-110m.json"

# Palette chosen to stay readable on the dark background
CAT_COLORS = ['#38bdf8', '#a78bfa', '#f472b6', '#fbbf24', '#34d399']
COUNTRY_COLORS = ['#2dd4bf', '#fb923c', '#60a5fa', '#e879f9', '#facc15']
INK, MUTED, GRID, PANEL = '#e6edf7', '#8b9ab3', '#23304a', '#131c2e'

st.markdown("""
<style>
  .block-container {padding-top: 2.2rem; max-width: 1250px;}
  .hero {padding: 1.4rem 1.6rem; border-radius: 16px; margin-bottom: 1.2rem;
         background: linear-gradient(120deg, #0f766e 0%, #1d4ed8 55%, #6d28d9 100%);}
  .hero h1 {margin: 0; font-size: 2rem; color: #fff; letter-spacing: -0.5px;}
  .hero p {margin: .35rem 0 0; color: #dbeafe; font-size: .98rem;}
  div[data-testid="stMetric"] {background: #131c2e; border: 1px solid #23304a;
         border-radius: 14px; padding: .9rem 1.1rem;}
  div[data-testid="stMetricLabel"] p {color: #8b9ab3; font-size: .8rem;
         text-transform: uppercase; letter-spacing: .06em;}
  div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 16px;}
  .hint {color: #8b9ab3; font-size: .9rem; margin: 0 0 .6rem;}
  .hint b {color: #2dd4bf;}
  section[data-testid="stSidebar"] {border-right: 1px solid #23304a;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def make_data(n: int = 200) -> pd.DataFrame:
    # Fixed seed so the app does not reshuffle on every Streamlit rerun
    rng = np.random.default_rng(42)
    country = rng.choice(COUNTRIES, size=n)
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


def style(chart):
    """Apply one dark look to every chart so the examples feel like a single product."""
    return (chart
            .configure(background='transparent')
            .configure_view(stroke=None)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=GRID,
                            domainColor=GRID, tickColor=GRID, labelFontSize=11, titleFontSize=12)
            .configure_legend(labelColor=INK, titleColor=MUTED, labelFontSize=12, orient='right')
            .configure_title(color=INK))


def show(chart):
    st.altair_chart(style(chart), width='stretch', theme=None)


def hint(text: str):
    st.markdown(f'<p class="hint">{text}</p>', unsafe_allow_html=True)


data = make_data()
cat_color = alt.Color('Product Category:N',
                      scale=alt.Scale(domain=CATEGORIES, range=CAT_COLORS),
                      legend=alt.Legend(title='Category'))
country_color = alt.Color('Country:N', scale=alt.Scale(domain=COUNTRIES, range=COUNTRY_COLORS))

# ---------------------------------------------------------------- header + KPIs
st.markdown("""
<div class="hero">
  <h1>Linked Views</h1>
  <p>Select data in one chart and watch the others respond &middot; Streamlit + Altair interactive selections</p>
</div>
""", unsafe_allow_html=True)

top = data.groupby('Product Category')['Sales'].sum().idxmax()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total sales", f"{data['Sales'].sum():,}")
k2.metric("Avg price", f"${data['Price'].mean():.0f}")
k3.metric("Units sold", f"{data['Quantity'].sum():,}")
k4.metric("Top category", top)
st.write("")

example = st.sidebar.radio("Choose an example", ["Bar + Scatter", "Line + Histogram", "Pie + Bar", "Map + Scatter"])
st.sidebar.markdown("---")
st.sidebar.caption("**How to interact**  \nClick or shift-click to select, drag to brush, click empty space to clear.")

# ---------------------------------------------------------------- examples
if example == "Bar + Scatter":
    with st.container(border=True):
        st.subheader("Bar chart → Scatter plot")
        hint("<b>Click</b> a bar (shift-click for several) to filter the scatter by category.")
        pick = alt.selection_point(fields=['Product Category'])

        bar = alt.Chart(data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X('Product Category:N', title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y('sum(Sales):Q', title='Total sales'),
            color=cat_color,
            opacity=alt.condition(pick, alt.value(1), alt.value(0.25)),
            tooltip=['Product Category', alt.Tooltip('sum(Sales):Q', title='Sales')],
        ).add_params(pick).properties(height=260, title='Sales by category')

        scatter = alt.Chart(data).mark_circle(size=70, opacity=0.85).encode(
            x=alt.X('Price:Q', title='Price'), y=alt.Y('Quantity:Q', title='Quantity'),
            color=cat_color, tooltip=['Product Category', 'Price', 'Quantity'],
        ).transform_filter(pick).properties(height=260, title='Price vs quantity')

        show(alt.vconcat(bar, scatter, spacing=24))

elif example == "Line + Histogram":
    with st.container(border=True):
        st.subheader("Line chart → Histogram")
        hint("<b>Drag</b> across the line chart to brush a range of records; the histogram counts only that range.")
        brush = alt.selection_interval(encodings=['x'])

        line = alt.Chart(data).mark_line(point=alt.OverlayMarkDef(size=25), strokeWidth=1.5).encode(
            x=alt.X('Index:Q', title='Record'), y=alt.Y('Price:Q', title='Price'),
            color=cat_color, tooltip=['Index', 'Product Category', 'Price'],
        ).add_params(brush).properties(height=250, title='Price per record')

        hist = alt.Chart(data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X('Quantity:Q', bin=alt.Bin(maxbins=10), title='Quantity'),
            y=alt.Y('count():Q', title='Records'), color=cat_color,
        ).transform_filter(brush).properties(height=250, title='Quantity distribution (brushed range)')

        show(alt.vconcat(line, hist, spacing=24))

elif example == "Pie + Bar":
    with st.container(border=True):
        st.subheader("Pie chart → Bar chart")
        hint("<b>Click</b> a slice to see that category's sales by country.")
        pick = alt.selection_point(fields=['Product Category'])

        pie = alt.Chart(data).mark_arc(innerRadius=62, outerRadius=130, stroke='#0b1220', strokeWidth=2).encode(
            theta='sum(Sales):Q', color=cat_color,
            opacity=alt.condition(pick, alt.value(1), alt.value(0.25)),
            tooltip=['Product Category', alt.Tooltip('sum(Sales):Q', title='Sales')],
        ).add_params(pick).properties(height=300, title='Sales share')

        bars = alt.Chart(data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X('Country:N', title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y('sum(Sales):Q', title='Sales'),
            color=country_color, tooltip=['Country', alt.Tooltip('sum(Sales):Q', title='Sales')],
        ).transform_filter(pick).properties(width=250, height=300, title='Sales by country')

        # Concat charts share colour scales by default; the pie's is pinned to product
        # categories, so country bars would get no colour. Keep the scales separate.
        show(alt.hconcat(pie, bars, spacing=20).resolve_scale(color='independent'))

elif example == "Map + Scatter":
    with st.container(border=True):
        st.subheader("Map → Scatter plot")
        hint("<b>Click</b> points on the map (shift-click for several) to select a country; the scatter shows only those sales.")
        pick = alt.selection_point(fields=['Country'])
        proj = dict(type='mercator', scale=640, center=[110, 5])

        base = alt.Chart(alt.topo_feature(WORLD_URL, 'countries')).mark_geoshape(
            fill='#1c2942', stroke='#0b1220', strokeWidth=0.6
        ).project(**proj).properties(width=560, height=360)

        points = alt.Chart(data).mark_circle(size=65).encode(
            longitude='Longitude:Q', latitude='Latitude:Q', color=cat_color,
            opacity=alt.condition(pick, alt.value(0.95), alt.value(0.12)),
            tooltip=['Country', 'Product Category', 'Sales'],
        ).add_params(pick).project(**proj)

        scatter = alt.Chart(data).mark_circle(size=65, opacity=0.85).encode(
            x='Sales:Q', y='Quantity:Q', color=cat_color,
            tooltip=['Country', 'Product Category', 'Sales', 'Quantity'],
        ).transform_filter(pick).properties(width=360, height=360, title='Sales vs quantity (selected)')

        show(alt.hconcat(base + points, scatter, spacing=30))

st.caption("DV Lab 3 · TFB3133/TEB3133 · Data is synthetic (seeded) for demonstration.")
