import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="Prompt Library (Viewer)", layout="wide", page_icon="📖")

# ==========================================
# 🎨 BULLETPROOF CSS OVERRIDE
# ==========================================
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 15%); }
    h1 {
        color: #0F172A !important;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-weight: 900 !important; 
        font-size: 3rem !important; 
        padding-bottom: 0px !important; margin-bottom: 0px !important;
    }
    button[role="tab"] {
        height: 55px !important;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto !important;
        font-weight: 700 !important; font-size: 20px !important; 
        color: #64748B !important; background-color: transparent !important;
        border-radius: 6px 6px 0 0 !important; padding: 0 24px !important;
    }
    button[role="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important; color: #0F172A !important;
        border-top: 5px solid #3B82F6 !important; /* Changed to Blue to indicate Viewer Mode */
        border-left: 1px solid #E2E8F0 !important; border-right: 1px solid #E2E8F0 !important;
        border-bottom: 2px solid #FFFFFF !important; font-weight: 900 !important; 
    }
    .block-container { padding-top: 2rem !important; }
    
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

def get_connection():
    return sqlite3.connect('advanced_prompt_library.db')

def get_safe_rating(val):
    if pd.isna(val) or val == '': return 3 
    if isinstance(val, bytes):
        try: return int.from_bytes(val, byteorder='little')
        except: return 3
    try: return int(float(val))
    except: return 3

# ==========================================
# 🗄️ SIDEBAR NAVIGATION & API SETTINGS
# ==========================================
st.sidebar.title("📖 Library Viewer")
st.sidebar.info("🔒 **Read-Only Mode**\nYou are viewing the live company prompt database. Edits are disabled.")
current_table = st.sidebar.radio("Navigation", ["📊 Analytics", "📝 Prompts", "⚙️ Tools", "🗂️ Projects", "🏷️ Tags"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API Settings")
st.sidebar.markdown("<span style='font-size: 0.8em; color: #666;'>Required to run prompts dynamically.</span>", unsafe_allow_html=True)
api_key = st.sidebar.text_input("OpenAI API Key", type="password", placeholder="sk-...")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Export")
try:
    conn_export = get_connection()
    df_export = pd.read_sql_query("SELECT * FROM prompts", conn_export)
    conn_export.close()
    if not df_export.empty:
        if 'performance_rating' in df_export.columns:
            df_export['performance_rating'] = df_export['performance_rating'].apply(get_safe_rating)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        st.sidebar.download_button(
            label="📥 Download Database (CSV)",
            data=csv_data, file_name=f"prompt_library_export_{timestamp}.csv", mime="text/csv", type="primary"
        )
except Exception as e:
    st.sidebar.error("Could not load export data.")

# ==========================================
# MODULE 0: ANALYTICS DASHBOARD
# ==========================================
if current_table == "📊 Analytics":
    st.title("📊 Visual Analytics Dashboard")
    
    conn = get_connection()
    df_analytics = pd.read_sql_query("SELECT * FROM prompts", conn)
    conn.close()
    
    if df_analytics.empty:
        st.info("The database is currently empty.")
    else:
        df_analytics['safe_rating'] = df_analytics['performance_rating'].apply(get_safe_rating)
        
        st.markdown("### 📈 High-Level Metrics")
        m1, m2, m3, m4 = st.columns(4)
        
        total_prompts = len(df_analytics)
        avg_rating = df_analytics['safe_rating'].mean()
        top_tool = df_analytics['tool'].mode()[0] if not df_analytics['tool'].dropna().empty else "N/A"
        top_model = df_analytics['model'].mode()[0] if not df_analytics['model'].dropna().empty else "N/A"
        
        m1.metric("Total Prompts", total_prompts)
        m2.metric("Average Rating", f"{avg_rating:.1f} ⭐" if pd.notna(avg_rating) else "N/A")
        m3.metric("Most Used Tool", top_tool)
        m4.metric("Most Used Model", top_model)
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🛠️ Prompts Distributed by Tool")
            tool_counts = df_analytics['tool'].value_counts()
            if not tool_counts.empty: st.bar_chart(tool_counts, color="#3B82F6") 
        with c2:
            st.markdown("##### 🗂️ Prompts Distributed by Project")
            proj_counts = df_analytics['project'].value_counts()
            if not proj_counts.empty: st.bar_chart(proj_counts, color="#10B981")
                
        st.divider()
        st.markdown("##### 🤖 Average Rating by AI Model")
        if not df_analytics['model'].dropna().empty:
            model_performance = df_analytics.groupby('model')['safe_rating'].mean()
            st.bar_chart(model_performance, color="#8B5CF6")

# ==========================================
# MODULE 1: PROMPTS MASTER TABLE
# ==========================================
elif current_table == "📝 Prompts":
    # Notice: Removed the Add and Manage tabs!
    tab1, tab3 = st.tabs(["🗂️ Prompts Library", "🚀 Compile & Run Variables"])

    with tab1:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM prompts ORDER BY id DESC", conn)
        conn.close()
        
        if not df.empty:
            st.markdown("<span style='font-size: 0.9em; color: #666;'>≡ View Settings</span>", unsafe_allow_html=True)
            v1, v2, v3 = st.columns([2,1,1])
            all_cols = ['prompt_name', 'full_prompt_text', 'tool', 'model', 'use_case', 'project', 'status', 'performance_rating', 'notes_learning', 'prompt_summary', 'improvements', 'created_date', 'last_modified']
            visible_cols = v1.multiselect("👁️ Visible Columns", options=all_cols, default=all_cols)
            filter_tool = v2.multiselect("Filter Tool", options=sorted(df['tool'].dropna().unique()), placeholder="Tool...")
            filter_proj = v3.multiselect("Filter Project", options=sorted(df['project'].dropna().unique()), placeholder="Project...")
            
            filtered_df = df.copy()
            if filter_tool: filtered_df = filtered_df[filtered_df['tool'].isin(filter_tool)]
            if filter_proj: filtered_df = filtered_df[filtered_df['project'].isin(filter_proj)]

            available_cols = [c for c in visible_cols if c in filtered_df.columns]
            display_df = filtered_df[available_cols].copy()
            
            if 'performance_rating' in display_df.columns:
                display_df['performance_rating'] = display_df['performance_rating'].apply(lambda x: '⭐' * get_safe_rating(x))
            
            st.divider()
            selection_event = st.dataframe(
                display_df, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="library_grid",
                column_config={
                    "prompt_name": st.column_config.TextColumn("A Prompt Name", width="medium"),
                    "full_prompt_text": st.column_config.TextColumn("📝 Full Prompt Text", width="large"),
                    "tool": st.column_config.TextColumn("⚙️ Tool", width="small"),
                    "model": st.column_config.TextColumn("A Model", width="small"),
                    "use_case": st.column_config.TextColumn("🏷️ Tag", width="medium"),
                    "project": st.column_config.TextColumn("🗂️ Project", width="medium"),
                    "status": st.column_config.TextColumn("✅ Status", width="small"),
                    "performance_rating": st.column_config.TextColumn("⭐ Rating", width="small"),
                    "notes_learning": st.column_config.TextColumn("📓 Notes", width="large"),
                    "prompt_summary": st.column_config.TextColumn("✨ Prompt Summary", width="medium"),
                    "improvements": st.column_config.TextColumn("✨ Improvements", width="medium"),
                    "created_date": st.column_config.TextColumn("📅 Created Date", width="small"),
                    "last_modified": st.column_config.TextColumn("📅 Last Modified", width="small")
                }
            )
            
            st.divider()
            st.subheader("🔍 Quick Reader")
            selected_rows = selection_event.selection.rows
            if len(selected_rows) > 0:
                selected_index = selected_rows[0]
                prompt_title = filtered_df.iloc[selected_index]['prompt_name']
                full_text = filtered_df.iloc[selected_index]['full_prompt_text']
                st.markdown(f"**📖 Currently Reading:** {prompt_title}")
                st.info(full_text)
            else:
                st.markdown("*Select a row in the grid above to read the full prompt here.*")
        else:
            st.info("The database is empty.")

    with tab3:
        conn = get_connection()
        compile_df = pd.read_sql_query("SELECT id, prompt_name, full_prompt_text FROM prompts", conn)
        conn.close()
        if not compile_df.empty:
            compile_dict = dict(zip(compile_df['id'], compile_df['prompt_name']))
            selected_id = st.selectbox("Select Prompt to Compile", options=compile_dict.keys(), format_func=lambda x: compile_dict[x])
            base_text = compile_df.loc[compile_df['id'] == selected_id, 'full_prompt_text'].values[0]
            with st.expander("View Base Template"): st.info(base_text)
            
            variables = list(set(re.findall(r'\[(.*?)\]', base_text)))
            compiled_text = base_text
            
            if variables:
                st.subheader("Fill in your variables:")
                user_inputs = {var: st.text_area(f"Value for [{var}]:", height=100) for var in variables}
                st.divider()
                
                for var, user_val in user_inputs.items():
                    if user_val: compiled_text = compiled_text.replace(f"[{var}]", user_val)
                st.markdown("**Final Compiled Prompt:**")
                st.code(compiled_text, language="markdown")
            else:
                st.success("No variables detected. Prompt is ready to run!")
                st.code(base_text, language="markdown")
                
            st.markdown("---")
            st.markdown("### 🤖 Execute Prompt Live")
            col_api1, col_api2 = st.columns([1, 2])
            run_model = col_api1.selectbox("Select OpenAI Model:", ["gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo"])
            
            if st.button("🚀 Run Prompt against AI", type="primary"):
                if not api_key:
                    st.error("⚠️ Please paste your OpenAI API Key in the left sidebar first!")
                else:
                    try:
                        import openai
                        client = openai.OpenAI(api_key=api_key)
                        with st.spinner(f"🧠 {run_model} is thinking..."):
                            response = client.chat.completions.create(
                                model=run_model,
                                messages=[
                                    {"role": "system", "content": "You are a helpful assistant."},
                                    {"role": "user", "content": compiled_text}
                                ]
                            )
                        st.success("✅ AI Response:")
                        st.info(response.choices[0].message.content)
                        
                    except ImportError:
                        st.error("❌ 'openai' package not found. Please run `pip install openai` in your terminal.")
                    except Exception as e:
                        st.error(f"❌ Error communicating with OpenAI: {e}")

# ==========================================
# MODULE 2: TOOLS TABLE
# ==========================================
elif current_table == "⚙️ Tools":
    st.title("⚙️ Tools Registry")
    conn = get_connection()
    df_tools = pd.read_sql_query("SELECT * FROM tools ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_tools, use_container_width=True, hide_index=True, column_config={"id": None})

# ==========================================
# MODULE 3: PROJECTS TABLE
# ==========================================
elif current_table == "🗂️ Projects":
    st.title("🗂️ Active Projects")
    conn = get_connection()
    df_proj = pd.read_sql_query("SELECT * FROM projects ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_proj, use_container_width=True, hide_index=True, column_config={"id": None})

# ==========================================
# MODULE 4: TAGS TABLE
# ==========================================
elif current_table == "🏷️ Tags":
    st.title("🏷️ Tags Dictionary")
    conn = get_connection()
    df_tags = pd.read_sql_query("SELECT * FROM tags ORDER BY id DESC", conn)
    conn.close()
    st.dataframe(df_tags, use_container_width=True, hide_index=True, column_config={"id": None})