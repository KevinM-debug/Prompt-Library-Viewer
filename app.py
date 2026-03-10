import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import re
import html 
from streamlit_quill import st_quill
from st_copy_to_clipboard import st_copy_to_clipboard

st.set_page_config(page_title="Prompt Library", layout="wide", page_icon="📝")

# ==========================================
# 🧹 HTML CLEANER FOR COPY BUTTON & API
# ==========================================
def clean_html_for_copy(raw_html):
    if not raw_html or pd.isna(raw_html): 
        return ""
    text = str(raw_html)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>|</li>|</blockquote>|</h1>|</h2>|</h3>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text

# ==========================================
# 🎨 BULLETPROOF CSS OVERRIDE
# ==========================================
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #F0FFF4 0%, #FFFFFF 15%); }
    h1 {
        color: #141414 !important;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-weight: 900 !important; 
        font-size: 3rem !important; 
        padding-bottom: 0px !important; margin-bottom: 0px !important;
    }
    button[role="tab"] {
        height: 55px !important;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto !important;
        font-weight: 700 !important; font-size: 20px !important; 
        color: #666666 !important; background-color: transparent !important;
        border-radius: 6px 6px 0 0 !important; padding: 0 24px !important;
    }
    button[role="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important; color: #141414 !important;
        border-top: 5px solid #18B85A !important; 
        border-left: 1px solid #D9D9D9 !important; border-right: 1px solid #D9D9D9 !important;
        border-bottom: 2px solid #FFFFFF !important; font-weight: 900 !important; 
    }
    .block-container { padding-top: 2rem !important; }
    
    .stMarkdown p { margin-bottom: 0.2rem !important; line-height: 1.5 !important; }
    .ql-editor p { margin-bottom: 0px !important; }
    .stMarkdown ul, .stMarkdown ol { margin-bottom: 0.2rem !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🗄️ SAFE DATABASE INITIALIZATION
# ==========================================
def get_connection():
    return sqlite3.connect('advanced_prompt_library.db', check_same_thread=False)

def initialize_database():
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt_name TEXT, full_prompt_text TEXT, tool TEXT, model TEXT, use_case TEXT, project TEXT, status TEXT, performance_rating INTEGER, prompt_summary TEXT, improvements TEXT, notes_learning TEXT, created_date TEXT, last_modified TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tools (id INTEGER PRIMARY KEY AUTOINCREMENT, tool_name TEXT, tool_type TEXT, notes TEXT, official_website TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, description TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, tag_name TEXT, description TEXT, category_suggestion TEXT)''')
    
    c.execute("PRAGMA table_info(prompts)")
    existing_cols = [row[1] for row in c.fetchall()]
    if 'notes_learning' not in existing_cols:
        c.execute("ALTER TABLE prompts ADD COLUMN notes_learning TEXT")
        
    c.execute("PRAGMA table_info(tools)")
    tool_cols = [row[1] for row in c.fetchall()]
    if 'official_website' not in tool_cols:
        c.execute("ALTER TABLE tools ADD COLUMN official_website TEXT")

    conn.commit()
    conn.close()

initialize_database()

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def get_table_items(table_name, column_name):
    try:
        conn = get_connection()
        df = pd.read_sql_query(f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL", conn)
        conn.close()
        items = [item for item in df[column_name].tolist() if item and str(item).strip() != '']
        return sorted(list(set(items)))
    except Exception:
        return []

def get_safe_rating(val):
    if pd.isna(val) or val == '': return 3 
    if isinstance(val, bytes):
        try: return int.from_bytes(val, byteorder='little')
        except: return 3
    try: return int(float(val))
    except: return 3

tools_list = get_table_items('tools', 'tool_name') or ["Notion", "Figma", "Zapier", "Slack", "Trello", "Airtable"]
projects_list = get_table_items('projects', 'project_name') or ["Website Redesign", "Mobile App Launch"]
tags_list = get_table_items('tags', 'tag_name') or ["Summarization", "Email Writing", "Programming", "SEO"]
models_list = ["GPT-4", "ChatGPT (GPT-4o)", "NotebookLM", "Perplexity", "Gemini Advanced", "Claude 3.5 Sonnet", "Suno AI", "Other"]

# ==========================================
# 🗄️ SIDEBAR NAVIGATION & API SETTINGS
# ==========================================
st.sidebar.title("📚 Database Tables")
st.sidebar.markdown("Select an area to view or manage.")
current_table = st.sidebar.radio("Navigation", ["📊 Analytics", "📝 Prompts", "⚙️ Tools", "🗂️ Projects", "🏷️ Tags"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API Settings")
api_key = st.sidebar.text_input("OpenAI API Key", type="password", placeholder="sk-...")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💾 Backup & Export")

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
            data=csv_data,
            file_name=f"prompt_library_backup_{timestamp}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.sidebar.info("Database is empty. Nothing to export yet!")
except Exception:
    pass

# ==========================================
# MODULE 0: ANALYTICS DASHBOARD
# ==========================================
if current_table == "📊 Analytics":
    st.title("📊 Visual Analytics Dashboard")
    
    conn = get_connection()
    df_analytics = pd.read_sql_query("SELECT * FROM prompts", conn)
    conn.close()
    
    if df_analytics.empty:
        st.info("Your database is empty! Add some prompts to see your metrics come alive.")
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
            if not tool_counts.empty: st.bar_chart(tool_counts, color="#18B85A") 
                
        with c2:
            st.markdown("##### 🗂️ Prompts Distributed by Project")
            proj_counts = df_analytics['project'].value_counts()
            if not proj_counts.empty: st.bar_chart(proj_counts, color="#2563EB")
                
        st.divider()
        st.markdown("##### 🤖 Average Rating by AI Model")
        if not df_analytics['model'].dropna().empty:
            model_performance = df_analytics.groupby('model')['safe_rating'].mean()
            st.bar_chart(model_performance, color="#8B5CF6")

# ==========================================
# MODULE 1: PROMPTS MASTER TABLE
# ==========================================
elif current_table == "📝 Prompts":
    # 🔥 ADDED TAB 5 FOR A/B TESTING 🔥
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗂️ Prompts Grid", "➕ Log New Prompt", "🚀 Compile Variables", "⚙️ Manage & Edit", "⚖️ A/B Testing"])

    with tab1:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM prompts ORDER BY id DESC", conn)
        conn.close()
        
        if not df.empty:
            st.markdown("<span style='font-size: 0.9em; color: #666;'>≡ View Settings & Search</span>", unsafe_allow_html=True)
            
            search_query = st.text_input("🔍 Global Search", placeholder="Search keywords in names, text, summaries, or notes...")
            
            v1, v2, v3 = st.columns([2,1,1])
            all_cols = ['prompt_name', 'full_prompt_text', 'tool', 'model', 'use_case', 'project', 'status', 'performance_rating', 'notes_learning', 'prompt_summary', 'improvements', 'created_date', 'last_modified']
            visible_cols = v1.multiselect("👁️ Visible Columns", options=all_cols, default=all_cols)
            filter_tool = v2.multiselect("Filter Tool", options=sorted(df['tool'].dropna().unique()), placeholder="Tool...")
            filter_proj = v3.multiselect("Filter Project", options=sorted(df['project'].dropna().unique()), placeholder="Project...")
            
            filtered_df = df.copy()
            
            if search_query:
                search_mask = (
                    filtered_df['prompt_name'].fillna('').str.contains(search_query, case=False, regex=False) |
                    filtered_df['full_prompt_text'].fillna('').str.contains(search_query, case=False, regex=False) |
                    filtered_df['prompt_summary'].fillna('').str.contains(search_query, case=False, regex=False) |
                    filtered_df['notes_learning'].fillna('').str.contains(search_query, case=False, regex=False)
                )
                filtered_df = filtered_df[search_mask]
            
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
                    "notes_learning": st.column_config.TextColumn("📓 Notes", width="large")
                }
            )
            
            st.divider()
            st.subheader("🔍 Quick Reader")
            selected_rows = selection_event.selection.rows
            
            if len(selected_rows) > 0 and selected_rows[0] < len(filtered_df):
                selected_index = selected_rows[0]
                row = filtered_df.iloc[selected_index]
                
                col_meta, col_text = st.columns([1, 2])
                
                with col_meta:
                    prompt_title = row.get('prompt_name', 'Unnamed Prompt')
                    st.markdown(f"### ✨ {prompt_title}")
                    
                    st.markdown("**✨ Summary:**")
                    summary = row.get('prompt_summary')
                    if pd.isna(summary) or not summary: summary = "---"
                    st.markdown(f'''<div style="resize: vertical; overflow: auto; height: 100px; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; background-color: white;">{summary}</div>''', unsafe_allow_html=True)
                    
                    st.markdown("**📓 Learning Notes:**")
                    notes = row.get('notes_learning')
                    if pd.isna(notes) or not notes: notes = "No notes recorded yet."
                    st.markdown(f'''<div style="resize: vertical; overflow: auto; height: 140px; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; background-color: white;">{notes}</div>''', unsafe_allow_html=True)

                    st.markdown("**💡 Suggested Improvements:**")
                    improvements_text = row.get('improvements')
                    if pd.isna(improvements_text) or not improvements_text: improvements_text = "No improvements suggested yet."
                    st.markdown(f'''<div style="resize: vertical; overflow: auto; height: 120px; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; background-color: white;">{improvements_text}</div>''', unsafe_allow_html=True)
                
                with col_text:
                    st.markdown("**📝 Full Prompt Text:**")
                    full_text = row.get('full_prompt_text', 'No text found.')
                    
                    st.markdown(f'''
                    <div style="resize: vertical; overflow: auto; height: 440px; border: 1px solid rgba(49, 51, 63, 0.2); border-radius: 0.5rem; padding: 1rem; background-color: white; margin-bottom: 15px;">
                        {full_text}
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    clean_text_to_copy = clean_html_for_copy(full_text)
                    st_copy_to_clipboard(text=clean_text_to_copy, before_copy_label="📋 Copy Raw Prompt", after_copy_label="✅ Copied!")
                        
            else:
                st.info("💡 Select a row in the grid above to read the full prompt, summary, notes, and improvements here.")
        else:
            st.info("Database is empty. Add a prompt in the 'Log New Prompt' tab!")

    with tab2:
        with st.form("add_form"):
            prompt_name = st.text_input("A Prompt Name*")
            c1, c2, c3, c4 = st.columns(4)
            tool_sel = c1.selectbox("⚙️ Tool", tools_list)
            model_sel = c2.selectbox("A Model", models_list)
            use_sel = c3.selectbox("🏷️ Tag", tags_list)
            proj_sel = c4.selectbox("🗂️ Project", projects_list)
            
            st.markdown("**📝 Full Prompt Text***")
            full_prompt_text = st_quill(placeholder="Type or paste your formatted prompt here...", html=True, key="quill_new")
            
            st.markdown("**✨ Prompt Summary (Optional)**")
            prompt_summary = st_quill(placeholder="Quick summary of the prompt...", html=True, key="quill_summary_new")
            
            st.markdown("**📓 Notes & Learnings**")
            notes_learning = st_quill(placeholder="Type or paste notes here...", html=True, key="quill_notes_new")
            
            st.markdown("**💡 Suggested Improvements (Optional)**")
            improvements = st_quill(placeholder="How could this prompt be improved next time?", html=True, key="quill_improvements_new")
            
            c9, c10 = st.columns(2)
            status = c9.selectbox("✅ Status", ["Active", "Draft", "Archived"])
            performance_rating = c10.slider("⭐ Rating (1-5)", 1, 5, 4)
            
            submit_btn = st.form_submit_button("Save Prompt")
            if submit_btn and prompt_name and full_prompt_text:
                current_time = datetime.now().strftime("%m/%d/%Y %I:%M%p").lower()
                conn = get_connection()
                c = conn.cursor()
                c.execute('''INSERT INTO prompts (prompt_name, full_prompt_text, tool, model, use_case, project, status, performance_rating, prompt_summary, improvements, notes_learning, created_date, last_modified) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                          (prompt_name, full_prompt_text, tool_sel, model_sel, use_sel, proj_sel, status, performance_rating, prompt_summary, improvements, notes_learning, current_time, current_time))
                conn.commit()
                conn.close()
                st.success(f"Prompt '{prompt_name}' saved!")
                st.rerun()

    with tab3:
        conn = get_connection()
        compile_df = pd.read_sql_query("SELECT id, prompt_name, full_prompt_text FROM prompts", conn)
        conn.close()
        if not compile_df.empty:
            compile_dict = dict(zip(compile_df['id'], compile_df['prompt_name']))
            selected_id = st.selectbox("Select Prompt to Compile", options=compile_dict.keys(), format_func=lambda x: compile_dict[x])
            
            # Use the HTML cleaner so the API doesn't get confused by Quill formatting
            base_text = clean_html_for_copy(compile_df.loc[compile_df['id'] == selected_id, 'full_prompt_text'].values[0])
            
            with st.expander("View Base Template"): 
                st.text(base_text)
            
            variables = list(set(re.findall(r'\[(.*?)\]', base_text)))
            compiled_text = base_text
            
            if variables:
                st.subheader("Fill in your variables:")
                user_inputs = {var: st.text_input(f"Value for [{var}]:") for var in variables}
                st.divider()
                
                for var, user_val in user_inputs.items():
                    if user_val: compiled_text = compiled_text.replace(f"[{var}]", user_val)
                st.markdown("**Final Compiled Prompt:**")
                st.text(compiled_text)
            else:
                st.success("No variables detected. Prompt is ready to run!")
                st.text(base_text)
        else:
            st.info("Add some prompts in the previous tab to compile them!")

    with tab4:
        conn = get_connection()
        edit_df = pd.read_sql_query("SELECT * FROM prompts ORDER BY id DESC", conn)
        conn.close()
        
        if not edit_df.empty:
            selection_event_edit = st.dataframe(
                edit_df[['id', 'prompt_name', 'tool', 'use_case', 'project', 'status']], 
                use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="manage_grid",
                column_config={"id": None}
            )
            selected_edit_rows = selection_event_edit.selection.rows
            
            if len(selected_edit_rows) > 0 and selected_edit_rows[0] < len(edit_df):
                selected_index = selected_edit_rows[0]
                edit_id = int(edit_df.iloc[selected_index]['id'])
                row_data = edit_df[edit_df['id'] == edit_id].iloc[0]
                
                with st.expander(f"⚙️ Editing: {row_data.get('prompt_name', 'Unnamed')}", expanded=True):
                    with st.form("edit_form"):
                        col_edit_meta, col_edit_text = st.columns([1, 2])
                        
                        def get_idx(val, lst): return lst.index(val) if val in lst else 0
                        
                        with col_edit_meta:
                            new_name = st.text_input("Prompt Name*", value=row_data.get('prompt_name', ''))
                            edit_tool = st.selectbox("⚙️ Tool", tools_list, index=get_idx(row_data.get('tool'), tools_list))
                            edit_model = st.selectbox("🤖 Model", models_list, index=get_idx(row_data.get('model'), models_list))
                            edit_use = st.selectbox("🏷️ Tag", tags_list, index=get_idx(row_data.get('use_case'), tags_list))
                            edit_proj = st.selectbox("🗂️ Project", projects_list, index=get_idx(row_data.get('project'), projects_list))
                            
                            st.markdown("**✨ Prompt Summary**")
                            edit_summary = st_quill(value=row_data.get('prompt_summary', ''), html=True, key=f"quill_edit_summary_{edit_id}")
                            
                            edit_status = st.selectbox("✅ Status", ["Active", "Draft", "Archived"], index=get_idx(row_data.get('status'), ["Active", "Draft", "Archived"]))
                            safe_rating = get_safe_rating(row_data.get('performance_rating'))
                            edit_rating = st.slider("⭐ Rating", 1, 5, safe_rating)
                        
                        with col_edit_text:
                            st.markdown("**📝 Full Prompt Text**")
                            new_text = st_quill(value=row_data.get('full_prompt_text', ''), html=True, key=f"quill_edit_text_{edit_id}")
                            
                            st.markdown("**📓 Learning Notes**")
                            edit_notes = st_quill(value=row_data.get('notes_learning', ''), html=True, key=f"quill_edit_notes_{edit_id}")
                            
                            st.markdown("**💡 Suggested Improvements**")
                            edit_improvements = st_quill(value=row_data.get('improvements', ''), html=True, key=f"quill_edit_improvements_{edit_id}")
                        
                        st.divider()
                        if st.form_submit_button("💾 Update Prompt", type="primary"):
                            current_time = datetime.now().strftime("%m/%d/%Y %I:%M%p").lower()
                            conn = get_connection()
                            conn.execute('''UPDATE prompts SET prompt_name=?, full_prompt_text=?, tool=?, model=?, use_case=?, project=?, status=?, performance_rating=?, prompt_summary=?, improvements=?, notes_learning=?, last_modified=? WHERE id=?''', 
                                      (new_name, new_text, edit_tool, edit_model, edit_use, edit_proj, edit_status, edit_rating, edit_summary, edit_improvements, edit_notes, current_time, edit_id))
                            conn.commit()
                            conn.close()
                            st.success("Prompt updated!")
                            st.rerun()
                    
                    st.markdown("---")
                    st.markdown("##### ⚡ Prompt Actions")
                    col_dup, col_del = st.columns(2)
                    
                    if col_dup.button("📑 Duplicate This Prompt"):
                        conn = get_connection()
                        c = conn.cursor()
                        new_prompt_name = row_data.get('prompt_name', 'Prompt') + " (Copy)"
                        current_time = datetime.now().strftime("%m/%d/%Y %I:%M%p").lower()
                        safe_dup_rating = get_safe_rating(row_data.get('performance_rating'))
                        
                        c.execute('''INSERT INTO prompts 
                                     (prompt_name, full_prompt_text, tool, model, use_case, project, status, performance_rating, prompt_summary, improvements, notes_learning, created_date, last_modified) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                                  (new_prompt_name, row_data.get('full_prompt_text', ''), row_data.get('tool', ''), row_data.get('model', ''), 
                                   row_data.get('use_case', ''), row_data.get('project', ''), "Draft", safe_dup_rating, 
                                   row_data.get('prompt_summary', ''), row_data.get('improvements', ''), row_data.get('notes_learning', ''), 
                                   current_time, current_time))
                        conn.commit()
                        conn.close()
                        st.success(f"Successfully duplicated! Look for '{new_prompt_name}' in the grid.")
                        st.rerun()

                    if col_del.button("🗑️ Delete This Prompt"):
                        conn = get_connection()
                        conn.execute("DELETE FROM prompts WHERE id=?", (edit_id,))
                        conn.commit()
                        conn.close()
                        st.warning("Prompt deleted.")
                        st.rerun()
        else:
            st.info("No prompts to manage. Log a new prompt first!")

    # ==========================================
    # 🔥 MODULE 1 / TAB 5: A/B TESTING 🔥
    # ==========================================
    with tab5:
        st.markdown("### ⚖️ A/B Test Your Prompts")
        st.markdown("Compare how two different AI models respond to the exact same prompt.")
        
        conn = get_connection()
        ab_df = pd.read_sql_query("SELECT id, prompt_name, full_prompt_text FROM prompts", conn)
        conn.close()
        
        if not ab_df.empty:
            ab_dict = dict(zip(ab_df['id'], ab_df['prompt_name']))
            ab_selected_id = st.selectbox("Select Prompt to Test", options=ab_dict.keys(), format_func=lambda x: ab_dict[x])
            
            # Clean HTML out of the text before parsing variables or sending to AI
            ab_base_text = clean_html_for_copy(ab_df.loc[ab_df['id'] == ab_selected_id, 'full_prompt_text'].values[0])
            
            ab_variables = list(set(re.findall(r'\[(.*?)\]', ab_base_text)))
            ab_compiled_text = ab_base_text
            
            if ab_variables:
                st.markdown("**Fill in your variables for the test:**")
                ab_cols = st.columns(3) # Create up to 3 columns for variables
                ab_inputs = {}
                for i, var in enumerate(ab_variables):
                    with ab_cols[i % 3]:
                        ab_inputs[var] = st.text_input(f"Value for [{var}]:", key=f"ab_{var}")
                
                for var, user_val in ab_inputs.items():
                    if user_val: ab_compiled_text = ab_compiled_text.replace(f"[{var}]", user_val)
            
            with st.expander("👀 View Compiled Prompt Being Tested"):
                st.text(ab_compiled_text)
                
            st.divider()
            
            # --- MODEL SELECTION & EXECUTION ---
            st.markdown("### 🤖 Select Models to Compare")
            api_models = ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
            col_mod1, col_mod2 = st.columns(2)
            
            ab_model_A = col_mod1.selectbox("Model A:", api_models, index=0)
            ab_model_B = col_mod2.selectbox("Model B:", api_models, index=2) # Defaults to gpt-3.5
            
            if st.button("🚀 Run A/B Test", type="primary"):
                if not api_key:
                    st.error("⚠️ Please paste your OpenAI API Key in the left sidebar first!")
                else:
                    try:
                        import openai
                        client = openai.OpenAI(api_key=api_key)
                        
                        st.markdown("---")
                        res_col1, res_col2 = st.columns(2)
                        
                        # --- RUN MODEL A ---
                        with res_col1:
                            st.markdown(f"**🟢 {ab_model_A} Response:**")
                            with st.spinner("Thinking..."):
                                response_A = client.chat.completions.create(
                                    model=ab_model_A,
                                    messages=[
                                        {"role": "system", "content": "You are a helpful assistant."},
                                        {"role": "user", "content": ab_compiled_text}
                                    ]
                                )
                                st.info(response_A.choices[0].message.content)
                                
                        # --- RUN MODEL B ---
                        with res_col2:
                            st.markdown(f"**🔵 {ab_model_B} Response:**")
                            with st.spinner("Thinking..."):
                                response_B = client.chat.completions.create(
                                    model=ab_model_B,
                                    messages=[
                                        {"role": "system", "content": "You are a helpful assistant."},
                                        {"role": "user", "content": ab_compiled_text}
                                    ]
                                )
                                st.success(response_B.choices[0].message.content)
                                
                    except ImportError:
                        st.error("❌ 'openai' package not found. Please run `pip install openai` in your terminal.")
                    except Exception as e:
                        st.error(f"❌ Error communicating with OpenAI: {e}")
        else:
            st.info("Add some prompts first to start testing!")

# ==========================================
# MODULE 2: TOOLS TABLE
# ==========================================
elif current_table == "⚙️ Tools":
    st.title("⚙️ Tool Management")
    t1, t2 = st.tabs(["🗂️ Tools Grid", "➕ Add New Tool"])
    with t1:
        conn = get_connection()
        df_tools = pd.read_sql_query("SELECT * FROM tools ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_tools, use_container_width=True, hide_index=True, column_config={"id": None})
    with t2:
        with st.form("tool_form"):
            new_tool = st.text_input("Tool Name*")
            tool_type = st.text_input("Tool Type (e.g., Productivity, AI)")
            website = st.text_input("Official Website")
            
            st.markdown("**Tool Notes**")
            notes = st_quill(placeholder="What is this tool used for?", html=True, key="quill_tool_notes")
            
            if st.form_submit_button("Save Tool") and new_tool:
                conn = get_connection()
                conn.execute("INSERT INTO tools (tool_name, tool_type, notes, official_website) VALUES (?, ?, ?, ?)", (new_tool, tool_type, notes, website))
                conn.commit()
                conn.close()
                st.success("Tool added!")
                st.rerun()

# ==========================================
# MODULE 3: PROJECTS TABLE
# ==========================================
elif current_table == "🗂️ Projects":
    st.title("🗂️ Project Management")
    p1, p2 = st.tabs(["🗂️ Projects Grid", "➕ Add New Project"])
    with p1:
        conn = get_connection()
        df_proj = pd.read_sql_query("SELECT * FROM projects ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_proj, use_container_width=True, hide_index=True, column_config={"id": None})
    with p2:
        with st.form("proj_form"):
            new_proj = st.text_input("Project Name*")
            status = st.selectbox("Status", ["Planning", "In Progress", "Completed"])
            
            st.markdown("**Project Description**")
            desc = st_quill(placeholder="Describe the scope of the project...", html=True, key="quill_proj_desc")
            
            if st.form_submit_button("Save Project") and new_proj:
                conn = get_connection()
                conn.execute("INSERT INTO projects (project_name, description, status) VALUES (?, ?, ?)", (new_proj, desc, status))
                conn.commit()
                conn.close()
                st.success("Project added!")
                st.rerun()

# ==========================================
# MODULE 4: TAGS TABLE
# ==========================================
elif current_table == "🏷️ Tags":
    st.title("🏷️ Tags Management")
    tg1, tg2 = st.tabs(["🗂️ Tags Grid", "➕ Add New Tag"])
    with tg1:
        conn = get_connection()
        df_tags = pd.read_sql_query("SELECT * FROM tags ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_tags, use_container_width=True, hide_index=True, column_config={"id": None})
    with tg2:
        with st.form("tag_form"):
            new_tag = st.text_input("Tag Name*")
            category = st.text_input("Category Suggestion")
            
            st.markdown("**Tag Description**")
            desc = st_quill(placeholder="What kind of prompts fall under this tag?", html=True, key="quill_tag_desc")
            
            if st.form_submit_button("Save Tag") and new_tag:
                conn = get_connection()
                conn.execute("INSERT INTO tags (tag_name, description, category_suggestion) VALUES (?, ?, ?)", (new_tag, desc, category))
                conn.commit()
                conn.close()
                st.success("Tag added!")
                st.rerun()