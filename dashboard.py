import streamlit as st
import redis
import json
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Semantic LLM Gateway Metrics", layout="wide")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

def get_data():
    try:
        # Connect to Upstash Redis
        client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Retrieve queries list
        raw_queries = client.lrange("gateway_queries", 0, 99)
        if not raw_queries:
            return pd.DataFrame(), {}
            
        queries = [json.loads(q) for q in raw_queries]
        df = pd.DataFrame(queries)
        
        # Retrieve aggregated stats
        aggregates = {
            "total_saved": float(client.get("gateway_metric:total_cost_saved") or 0.0),
            "total_spent": float(client.get("gateway_metric:total_cost_spent") or 0.0),
            "total_requests": int(client.get("gateway_metric:total_requests") or 0),
            "cache_hits": int(client.get("gateway_metric:cache_hits") or 0),
            "total_latency": float(client.get("gateway_metric:total_latency") or 0.0)
        }
        return df, aggregates
    except Exception as e:
        st.error(f"Failed to query database: {e}")
        return pd.DataFrame(), {}

st.title("Semantic LLM Gateway & Cost-Aware Routing Proxy")
st.subheader("Observability Dashboard")

df, stats = get_data()

if df.empty:
    st.info("No metrics data available in Upstash Redis yet. Make some requests to the Gateway!")
    if st.button("Refresh Data"):
        st.rerun()
else:
    # Top Level Metrics Row
    total_saved = stats.get("total_saved", 0.0)
    total_spent = stats.get("total_spent", 0.0)
    total_requests = stats.get("total_requests", 0)
    cache_hits = stats.get("cache_hits", 0)
    hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0.0
    
    # Calculate average latency from total latency / total requests
    total_latency = stats.get("total_latency", 0.0)
    avg_latency = total_latency / total_requests if total_requests > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Cost Saved ($)", value=f"${total_saved:.6f}")
    with col2:
        st.metric(label="Total Cost Spent ($)", value=f"${total_spent:.6f}")
    with col3:
        st.metric(label="Cache Hit Rate (%)", value=f"{hit_rate:.2f}%")
    with col4:
        st.metric(label="Average Latency (ms)", value=f"{avg_latency:.2f}")

    st.markdown("---")

    # Bar chart comparing latencies
    st.subheader("Latency Comparison: Cache Hit vs Live Groq")
    latency_summary = df.groupby('is_cache_hit')['latency_ms'].mean().reset_index()
    latency_summary['is_cache_hit'] = latency_summary['is_cache_hit'].map({1: 'Cache Hit', 0: 'Cache Miss (Live Groq)'})
    latency_summary.rename(columns={'is_cache_hit': 'Request Type', 'latency_ms': 'Avg Latency (ms)'}, inplace=True)
    st.bar_chart(data=latency_summary.set_index('Request Type'))

    st.markdown("---")

    # Live Dataframe showing the last 20 queries
    st.subheader("Recent Queries (Last 20)")
    recent_df = df.head(20).copy()
    
    # Format the dataframe for display
    display_df = recent_df[['timestamp', 'prompt', 'complexity', 'model_routed', 'is_cache_hit', 'latency_ms', 'cost_saved']]
    display_df['is_cache_hit'] = display_df['is_cache_hit'].apply(lambda x: "HIT" if x == 1 else "MISS")
    display_df['prompt'] = display_df['prompt'].apply(lambda x: x[:100] + "..." if len(x) > 100 else x)
    display_df['latency_ms'] = display_df['latency_ms'].round(2)
    display_df['cost_saved'] = display_df['cost_saved'].apply(lambda x: f"${x:.6f}")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Refresh button
    if st.button("Refresh Data"):
        st.rerun()
