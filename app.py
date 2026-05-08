import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Yelp Restaurant Intelligence", page_icon="🍽️", layout="wide")
st.title("🍽️ Yelp Restaurant Intelligence Dashboard")

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def get_connection():
    # Ensure yelp.db is in the same folder as this app.py file!
    return sqlite3.connect('yelp.db', check_same_thread=False)

conn = get_connection()

# --- 3. SIDEBAR: INTERACTIVE FILTERING ---
st.sidebar.header("Control Panel")
st.sidebar.write("Select a restaurant below to dynamically update the dashboard and run live statistical tests.")

@st.cache_data
def get_businesses():
    # Grabbing a sample of businesses for the dropdown
    return pd.read_sql_query("SELECT business_id, name FROM business LIMIT 100", conn)

business_df = get_businesses()
selected_name = st.sidebar.selectbox("Select a Restaurant:", business_df['name'])
selected_id = business_df[business_df['name'] == selected_name]['business_id'].iloc[0]


# --- 4. MULTI-TAB DASHBOARD LAYOUT ---
tab1, tab2 = st.tabs(["📊 Engagement Trends", "🧪 Advanced Research"])

# ==========================================
# TAB 1: CORE ENGAGEMENT METRICS
# ==========================================
with tab1:
    st.markdown(f"### Core Metrics for **{selected_name}**")
    
    # 1. Top Level Metric Cards
    stats_query = f"SELECT review_count, stars FROM business WHERE business_id = '{selected_id}'"
    business_stats = pd.read_sql_query(stats_query, conn)  # Renamed variable here!
    
    col1, col2 = st.columns(2)
    col1.metric("Total Reviews", business_stats['review_count'].iloc[0]) # Updated here
    col2.metric("Average Star Rating", business_stats['stars'].iloc[0])  # Updated here
    
    st.divider()
    
    # 2. Busiest Hours Chart
    st.subheader("Busiest Review Hours")
    hour_query = f"""
        SELECT cast(strftime('%H', date) as integer) as hour, COUNT(*) as review_count
        FROM review
        WHERE business_id = '{selected_id}'
        GROUP BY hour
    """
    hour_df = pd.read_sql_query(hour_query, conn)
    
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    sns.barplot(x='hour', y='review_count', data=hour_df, color='#F8862C', ax=ax1)
    ax1.set_title("Review Volume by Hour of the Day")
    ax1.set_xlabel("Hour of the Day (24H)")
    ax1.set_ylabel("Number of Reviews")
    st.pyplot(fig1)

# ==========================================
# TAB 2: STATISTICAL HYPOTHESIS TESTING
# ==========================================
with tab2:
    st.markdown(f"### Live Statistical Analysis for **{selected_name}**")
    
    # --- RESEARCH 1: THE RANT FACTOR ---
    st.subheader("1. The 'Rant Factor' (Customer Verbosity)")
    st.write("Does this specific restaurant drive customers to write massive essays (warnings), or quick praises?")
    
    query_tip_rant = f"""
        SELECT LENGTH(t.text) AS tip_length
        FROM tip t
        WHERE t.business_id = '{selected_id}'
    """
    tip_rant_df = pd.read_sql_query(query_tip_rant, conn)
    
    if len(tip_rant_df) > 5: 
        avg_length = tip_rant_df['tip_length'].mean()
        st.metric(label="Average Tip Character Length", value=f"{avg_length:.0f} characters")
        
        fig2, ax2 = plt.subplots(figsize=(8, 3))
        sns.histplot(tip_rant_df['tip_length'], bins=20, color='#E54F29', ax=ax2)
        ax2.set_title("Distribution of Customer Tip Lengths")
        st.pyplot(fig2)
    else:
        st.warning("Not enough tip data for this specific restaurant.")

    st.divider()

    # --- RESEARCH 2: WEEKEND FOOT TRAFFIC ---
    st.subheader("2. Weekend vs. Weekday Traffic Surge")
    st.write("Does this restaurant see a mathematically significant surge in physical foot traffic on the weekends?")
    
    query_weekend = f"SELECT date FROM checkin WHERE business_id = '{selected_id}'"
    checkin_df = pd.read_sql_query(query_weekend, conn)
    
    if len(checkin_df) > 0 and pd.notna(checkin_df['date'].iloc[0]):
        checkin_dates = [d.strip() for d in checkin_df['date'].iloc[0].split(',')]
        df_dates = pd.DataFrame(checkin_dates, columns=['datetime'])
        df_dates['datetime'] = pd.to_datetime(df_dates['datetime'])
        df_dates['date_only'] = df_dates['datetime'].dt.date
        df_dates['is_weekend'] = df_dates['datetime'].dt.day_name().isin(['Saturday', 'Sunday'])
        
        daily_checkins = df_dates.groupby(['date_only', 'is_weekend']).size().reset_index(name='checkin_count')
        weekend_counts = daily_checkins[daily_checkins['is_weekend'] == True]['checkin_count']
        weekday_counts = daily_checkins[daily_checkins['is_weekend'] == False]['checkin_count']
        
        col_w1, col_w2 = st.columns(2)
        col_w1.metric("Avg Daily Check-ins (Weekend)", f"{weekend_counts.mean():.1f}")
        col_w2.metric("Avg Daily Check-ins (Weekday)", f"{weekday_counts.mean():.1f}")
        
        if len(weekend_counts) > 2 and len(weekday_counts) > 2:
            t_stat, p_val = stats.ttest_ind(weekend_counts, weekday_counts, equal_var=False)
            if p_val < 0.05 and weekend_counts.mean() > weekday_counts.mean():
                st.success(f"**Conclusion:** Statistically significant (P-Value: {p_val:.3e}). You must increase weekend staffing.")
            else:
                st.info(f"**Conclusion:** Traffic is relatively balanced (P-Value: {p_val:.3e}). Standard staffing is fine.")
    else:
        st.warning("No check-in data available for this restaurant.")

    st.divider()

    # --- RESEARCH 3: ELITE INFLUENCE ---
    st.subheader("3. The 'Elite' Influence Factor")
    st.write("Does the Yelp community trust 'Elite' users more than average reviewers for this establishment?")
    
    query_elite = f"""
        SELECT 
            CASE WHEN u.elite = '' THEN 'Not Elite' ELSE 'Elite' END AS elite_status,
            r.useful
        FROM review r
        JOIN user u ON r.user_id = u.user_id
        WHERE r.business_id = '{selected_id}'
    """
    elite_df = pd.read_sql_query(query_elite, conn)
    
    if len(elite_df) > 0:
        elite_useful = elite_df[elite_df['elite_status'] == 'Elite']['useful']
        non_elite_useful = elite_df[elite_df['elite_status'] == 'Not Elite']['useful']
        
        avg_elite = elite_useful.mean() if len(elite_useful) > 0 else 0
        avg_non_elite = non_elite_useful.mean() if len(non_elite_useful) > 0 else 0
        
        col_e1, col_e2 = st.columns(2)
        col_e1.metric("Avg 'Useful' Votes per Elite Review", f"{avg_elite:.2f}")
        col_e2.metric("Avg 'Useful' Votes per Normal Review", f"{avg_non_elite:.2f}")
        
        if len(elite_useful) > 2 and len(non_elite_useful) > 2:
            t_stat_e, p_val_e = stats.ttest_ind(elite_useful, non_elite_useful, equal_var=False)
            if p_val_e < 0.05 and avg_elite > avg_non_elite:
                st.success(f"**Conclusion:** Statistically significant (P-Value: {p_val_e:.3e}). Elite reviews dictate your reputation here.")
            else:
                st.info(f"**Conclusion:** Elite status does not guarantee more 'Useful' votes for this restaurant.")
    else:
        st.warning("No review data available for this restaurant.")