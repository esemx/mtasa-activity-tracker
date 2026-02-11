import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet

st.set_page_config(
    page_title="MTA:SA Server Stats",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data(ttl=600)
def load_data():
    try:
        df = pd.read_csv("data/mta_history.csv")
        df['ds'] = pd.to_datetime(df['ds'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

st.title("MTA:SA Player Statistics")

if df.empty:
    st.error("No data available. Waiting for the first update from the servers.")
    st.stop()

st.markdown("### Current Status")

last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

current_ccu = last_row['y']
prev_ccu = prev_row['y']
ccu_delta = current_ccu - prev_ccu
ccu_pct = (ccu_delta / prev_ccu * 100) if prev_ccu != 0 else 0

current_servers = last_row['servers']

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Players Online", 
        value=f"{current_ccu:,}", 
        delta=f"{ccu_delta} ({ccu_pct:.1f}%)"
    )
with col2:
    st.metric(
        label="Active Servers", 
        value=f"{current_servers:,}", 
        delta=f"{int(current_servers - prev_row['servers'])}",
        delta_color="normal"
    )
with col3:
    peak_24h = df.tail(48)['y'].max() if len(df) > 48 else df['y'].max()
    st.metric(
        label="24h Peak", 
        value=f"{peak_24h:,}",
        help="Highest player count recorded in the last 24 hours"
    )
with col4:
    st.metric(
        label="Last Update", 
        value=last_row['ds'].strftime('%H:%M')
    )

st.divider()

st.markdown("### Traffic Forecast")

if len(df) < 20:
    st.info(f"More data is required to generate a forecast. (Currently {len(df)}/20 points).")
    fig = px.line(df, x='ds', y='y', title="Live Player Count")
    fig.update_layout(template="plotly_dark", xaxis_title="Time", yaxis_title="Players")
    st.plotly_chart(fig, width="stretch")
else:
    st.markdown("""
    This chart shows the predicted player count for the next 24 hours based on recent trends. 
    The dashed line represents the forecast, and the shaded area shows the expected range.
    """)
    
    with st.spinner('Calculating 24h forecast...'):
        m = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=24, freq='h')
        forecast = m.predict(future)

        last_hist_val = df.iloc[-1]['y']
        future_val = forecast.iloc[-1]['yhat']
        trend_diff = future_val - last_hist_val
        trend_direction = "increase" if trend_diff > 0 else "decrease"
        
        st.info(f"Summary: The model expects a net {trend_direction} of approximately {abs(int(trend_diff))} players over the next 24 hours.")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['ds'], y=df['y'], 
            name='Actual Players', 
            mode='lines',
            line=dict(color='#2E86C1', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast['ds'], y=forecast['yhat'], 
            name='Predicted Trend',
            mode='lines',
            line=dict(color='#D4AC0D', dash='dash', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
            y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
            fill='toself',
            fillcolor='rgba(212, 172, 13, 0.1)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            name='Confidence Range'
        ))

        fig.update_layout(
            template="plotly_dark", 
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
        )
        st.plotly_chart(fig, width="stretch")

st.divider()

st.markdown("### Peak Activity Times")
st.markdown("Heatmap showing player density by day and hour.")

if len(df) > 10:
    df['hour'] = df['ds'].dt.hour
    df['day_name'] = df['ds'].dt.day_name()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    heatmap_data = df.groupby(['day_name', 'hour'])['y'].mean().reset_index()
    
    fig_heat = px.density_heatmap(
        heatmap_data, x='hour', y='day_name', z='y', 
        nbinsx=24, 
        category_orders={"day_name": days_order},
        color_continuous_scale='Teal', 
        template="plotly_dark"
    )
    
    fig_heat.update_layout(
        xaxis_title="Hour of Day (UTC)",
        yaxis_title=None,
        coloraxis_colorbar=dict(title="Avg. Players")
    )
    st.plotly_chart(fig_heat, width="stretch")
else:
    st.text("Not enough data to generate the activity heatmap.")