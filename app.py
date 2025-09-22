import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from typing import Dict, List, Tuple, Any
import time

# Page config
st.set_page_config(
    page_title="User-Based SoD Conflict Analyzer", 
    page_icon="👤", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for attractive styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .conflict-card {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .success-card {
        background: linear-gradient(135deg, #00b894, #00cec9);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .info-card {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-card {
        background: linear-gradient(135deg, #fd79a8, #e84393);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff, #e8f0fe);
        margin: 1rem 0;
    }
    
    .tab-content {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# Helper: normalize colnames
def normalize_colname(col):
    return str(col).strip().lower().replace(" ", "_").replace("-", "_")

def load_user_data_from_upload(user_file):
    """Load user data from uploaded file"""
    try:
        if user_file.name.endswith('.csv'):
            user_data = pd.read_csv(user_file)
        else:
            # Handle Excel files
            excel_file = pd.ExcelFile(user_file)
            sheet_names = excel_file.sheet_names
            
            # Let user choose sheet if multiple sheets
            if len(sheet_names) > 1:
                sheet_name = st.selectbox(
                    "Select User Data Sheet:",
                    options=sheet_names,
                    help="Choose which sheet contains user data",
                    key="user_sheet_selector"
                )
            else:
                sheet_name = sheet_names[0]
            
            user_data = pd.read_excel(user_file, sheet_name=sheet_name)
        
        user_data.columns = [normalize_colname(c) for c in user_data.columns]
        return user_data
    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")
        return None

def load_role_tcode_mapping_from_upload(roles_file):
    """Load role-tcode mapping from uploaded file"""
    try:
        possible_sheets = ["Role Tcode Mapping", "Role Tcode Mapping_New", "User Mapping"]
        role_tcode_data = []
        excel_file = pd.ExcelFile(roles_file)
        available_sheets = excel_file.sheet_names
        
        # Let user select relevant sheets
        relevant_sheets = []
        for sheet in available_sheets:
            for possible in possible_sheets:
                if possible.lower() in sheet.lower():
                    relevant_sheets.append(sheet)
                    break
        
        if not relevant_sheets:
            relevant_sheets = available_sheets
        
        if len(relevant_sheets) > 1:
            selected_sheets = st.multiselect(
                "Select Role Mapping Sheets:",
                options=relevant_sheets,
                default=[relevant_sheets[0]],
                help="Choose sheets containing role-tcode mappings",
                key="role_sheets_selector"
            )
        else:
            selected_sheets = relevant_sheets
        
        for sheet_name in selected_sheets:
            df = pd.read_excel(roles_file, sheet_name=sheet_name)
            df.columns = [normalize_colname(c) for c in df.columns]

            role_cols = [col for col in df.columns if 'role' in col]
            tcode_cols = [col for col in df.columns if 'tcode' in col or 't_code' in col]

            if role_cols and tcode_cols:
                mapping_df = df[[role_cols[0], tcode_cols[0]]].dropna()
                mapping_df.columns = ['role', 'tcode']
                role_tcode_data.append(mapping_df)

        if role_tcode_data:
            combined_mapping = pd.concat(role_tcode_data, ignore_index=True)
            expanded_mapping = []
            for _, row in combined_mapping.iterrows():
                role = str(row['role']).strip().upper()
                tcodes = str(row['tcode']).strip()
                if tcodes and tcodes not in ['nan', 'NaN', '']:
                    for tcode in tcodes.split(','):
                        tcode = tcode.strip().upper()
                        if tcode:
                            expanded_mapping.append({'role': role, 'tcode': tcode})
            return pd.DataFrame(expanded_mapping).drop_duplicates()

        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading role mapping: {str(e)}")
        return None

def load_user_role_assignments_from_upload(user_data):
    """Extract user-role assignments from uploaded user data"""
    try:
        role_columns = [col for col in user_data.columns if 'role' in col]
        user_role_assignments = []

        if role_columns:
            for _, row in user_data.iterrows():
                user_id = str(row.get('user_id', '')).strip()
                user_name = str(row.get('user_name', '')).strip()
                for role_col in role_columns:
                    role = str(row.get(role_col, '')).strip().upper()
                    if role and role not in ['nan', 'NaN', '']:
                        user_role_assignments.append({
                            'user_id': user_id,
                            'user_name': user_name,
                            'role': role
                        })

        return pd.DataFrame(user_role_assignments).drop_duplicates()
    except Exception as e:
        st.error(f"Error extracting user roles: {str(e)}")
        return pd.DataFrame()

def create_user_tcode_mapping(user_roles, role_tcodes):
    """Create user-tcode mapping"""
    try:
        if user_roles.empty or role_tcodes.empty:
            return pd.DataFrame()
        user_tcodes = user_roles.merge(role_tcodes, on='role', how='inner')
        return user_tcodes
    except Exception as e:
        st.error(f"Error creating user-tcode mapping: {str(e)}")
        return pd.DataFrame()

def load_risk_data_from_upload(risk_file):
    """Load risk and function mapping data from uploaded file"""
    try:
        # Load Function T-Code Mapping
        function_map = pd.read_excel(risk_file, sheet_name="Function T-Code Mapping")
        function_map.columns = [normalize_colname(c) for c in function_map.columns]
        
        # Explicit column detection
        func_id_col = next((c for c in function_map.columns if c in ["function_id", "functionid"]), None)
        tcode_col = next((c for c in function_map.columns if "action" in c and ("tcode" in c or "t_codes" in c)), None)
        
        if not func_id_col:
            raise ValueError("Function ID column not found in Function T-Code Mapping sheet")
        if not tcode_col:
            raise ValueError("Action (T-Codes/Apps/Services) column not found in Function T-Code Mapping sheet")
        
        function_map = function_map[[func_id_col, tcode_col]].rename(
            columns={func_id_col: "function_id", tcode_col: "tcode"}
        )
        
        # Expand comma-separated tcodes
        expanded_functions = []
        for _, row in function_map.iterrows():
            function_id = str(row['function_id']).strip().upper()
            tcodes = str(row['tcode']).strip()
            if tcodes and tcodes.lower() not in ['nan', '']:
                for tcode in tcodes.split(','):
                    tcode = tcode.strip().upper()
                    if tcode:
                        expanded_functions.append({"function_id": function_id, "tcode": tcode})
        
        function_map_expanded = pd.DataFrame(expanded_functions).drop_duplicates()
        
        # Load Risk Function Mapping
        risk_pairs = pd.read_excel(risk_file, sheet_name="Risk Function Mapping")
        risk_pairs.columns = [normalize_colname(c) for c in risk_pairs.columns]
        
        conflict_cols = [c for c in risk_pairs.columns if "conflicting_function" in c]
        if not conflict_cols:
            raise ValueError("No conflicting_function columns found in Risk Function Mapping sheet")
        
        risk_function_pairs = []
        for _, row in risk_pairs.iterrows():
            risk_id = str(row.get("access_risk_id", "")).strip().upper()
            functions = []
            for col in conflict_cols:
                val = row[col]
                if pd.notna(val):
                    val = str(val).strip().upper()
                    if " - " in val:
                        val = val.split(" - ")[0].strip()
                    functions.append(val)
            
            functions = sorted(set(functions))
            for i in range(len(functions)):
                for j in range(i + 1, len(functions)):
                    risk_function_pairs.append({
                        "risk_id": risk_id,
                        "function_1": functions[i],
                        "function_2": functions[j]
                    })
        
        risk_pairs_df = pd.DataFrame(risk_function_pairs).drop_duplicates()
        
        # Add tcode info
        func_tcodes = function_map_expanded.groupby("function_id")["tcode"].apply(
            lambda x: ", ".join(sorted(set(x)))
        ).reset_index()
        
        risk_pairs_df = risk_pairs_df.merge(
            func_tcodes, left_on="function_1", right_on="function_id", how="left"
        ).rename(columns={"tcode": "tcode1"}).drop(columns=["function_id"])
        
        risk_pairs_df = risk_pairs_df.merge(
            func_tcodes, left_on="function_2", right_on="function_id", how="left"
        ).rename(columns={"tcode": "tcode2"}).drop(columns=["function_id"])
        
        return function_map_expanded, risk_pairs_df
    except Exception as e:
        st.error(f"Error loading risk data: {str(e)}")
        return None, None

def analyze_conflicts(user_tcodes, function_map, risk_pairs):
    """Main conflict analysis function"""
    try:
        if user_tcodes.empty:
            return pd.DataFrame()
        
        user_functions = user_tcodes.merge(function_map, on="tcode", how="inner")

        conflicts = user_functions.merge(risk_pairs, left_on="function_id", right_on="function_1", how="inner")
        conflicts = conflicts.merge(user_functions, left_on=["function_2", "user_id"], right_on=["function_id", "user_id"], how="inner", suffixes=("_f1", "_f2"))

        final_conflicts = conflicts[["user_id", "user_name_f1", "role_f1", "role_f2", "risk_id", "function_1", "function_2", "tcode1", "tcode2", "tcode_f1", "tcode_f2"]].drop_duplicates()
        return final_conflicts.rename(columns={"user_name_f1": "user_name", "role_f1": "role_1", "role_f2": "role_2", "tcode_f1": "user_tcode_f1", "tcode_f2": "user_tcode_f2"})
    except Exception as e:
        st.error(f"Error analyzing conflicts: {str(e)}")
        return pd.DataFrame()

def analyze_user_conflicts(user_id: str, user_tcodes, function_map, risk_pairs):
    """Analyze conflicts for a specific user"""
    try:
        user_id = str(user_id).strip()
        
        # Get user's data
        user_data_df = user_tcodes[user_tcodes["user_id"] == user_id]
        
        if user_data_df.empty:
            return {"user_id": user_id, "conflicts": [], "functions": [], "tcodes": [], "roles": [], "conflict_count": 0, "error": f"User {user_id} not found"}
        
        user_name = user_data_df["user_name"].iloc[0] if not user_data_df.empty else ""
        user_roles = list(user_data_df["role"].unique())
        user_tcodes_list = list(user_data_df["tcode"].unique())
        
        if len(user_tcodes_list) == 0:
            return {"user_id": user_id, "user_name": user_name, "conflicts": [], "functions": [], "tcodes": [], "roles": user_roles, "conflict_count": 0, "error": f"No T-codes found for user {user_id}"}
        
        # Map user's tcodes to functions
        user_func = user_data_df.merge(function_map, on="tcode", how="left")
        user_functions = list(user_func["function_id"].dropna().unique())
        
        conflicts = []
        
        # Track user's function access with roles
        user_function_access = {}
        for _, row in user_func.iterrows():
            if pd.notna(row["function_id"]):
                func_id = row["function_id"]
                role = row["role"]
                tcode = row["tcode"]
                
                if func_id not in user_function_access:
                    user_function_access[func_id] = {"roles": set(), "tcodes": set()}
                user_function_access[func_id]["roles"].add(role)
                user_function_access[func_id]["tcodes"].add(tcode)
        
        # Check conflicts by comparing user's functions with risk pairs
        processed_pairs = set()
        
        for _, risk_pair in risk_pairs.iterrows():
            func1_name = str(risk_pair.get("function_1", "")).strip()
            func2_name = str(risk_pair.get("function_2", "")).strip()
            risk_id = str(risk_pair.get("risk_id", "")).strip()
            
            # Skip invalid entries
            if not all([func1_name, func2_name, risk_id]) or \
               any(x in ["nan", "NaN", "None", ""] for x in [func1_name, func2_name, risk_id]):
                continue
            
            # Check if user has access to both conflicting functions
            if func1_name in user_function_access and func2_name in user_function_access:
                func_pair = tuple(sorted([func1_name, func2_name]))
                if func_pair not in processed_pairs:
                    processed_pairs.add(func_pair)
                    
                    func1_roles = list(user_function_access[func1_name]["roles"])
                    func2_roles = list(user_function_access[func2_name]["roles"])
                    func1_user_tcodes = list(user_function_access[func1_name]["tcodes"])
                    func2_user_tcodes = list(user_function_access[func2_name]["tcodes"])
                    
                    conflicts.append({
                        "type": f"SoD Violation ({risk_id})",
                        "function_1": func1_name,
                        "function_2": func2_name,
                        "description": f"User has access to conflicting functions: {func1_name} through roles {', '.join(func1_roles)} AND {func2_name} through roles {', '.join(func2_roles)}. This violates segregation of duties.",
                        "risk_id": risk_id,
                        "role_1": ", ".join(sorted(func1_roles)),
                        "role_2": ", ".join(sorted(func2_roles)),
                        "tcode_1": ", ".join(sorted(func1_user_tcodes)),
                        "tcode_2": ", ".join(sorted(func2_user_tcodes)),
                    })
        
        return {
            "user_id": user_id,
            "user_name": user_name,
            "roles": user_roles,
            "functions": user_functions,
            "tcodes": user_tcodes_list,
            "conflicts": conflicts,
            "conflict_count": len(conflicts)
        }
    except Exception as e:
        st.error(f"Error analyzing user conflicts: {str(e)}")
        return {"user_id": user_id, "conflicts": [], "functions": [], "tcodes": [], "roles": [], "conflict_count": 0, "error": str(e)}

def create_user_summary(conflicts_df, user_tcodes_df):
    """Create user summary with conflict information"""
    try:
        summary = []
        for user_id in user_tcodes_df['user_id'].unique():
            user_data = user_tcodes_df[user_tcodes_df['user_id'] == user_id]
            user_name = user_data['user_name'].iloc[0] if not user_data.empty else ""
            roles = list(user_data['role'].unique())
            tcodes = list(user_data['tcode'].unique())
            conflict_count = len(conflicts_df[conflicts_df['user_id'] == user_id]) if not conflicts_df.empty else 0
            summary.append({
                "user_id": user_id,
                "user_name": user_name,
                "roles": ", ".join(roles),
                "total_roles": len(roles),
                "total_tcodes": len(tcodes),
                "conflict_count": conflict_count,
                "risk_status": "HIGH RISK" if conflict_count > 0 else "SAFE"
            })
        return pd.DataFrame(summary)
    except Exception as e:
        st.error(f"Error creating user summary: {str(e)}")
        return pd.DataFrame()

def create_excel_report(conflicts_df, user_summary_df, user_tcodes_df, function_map_df, risk_pairs_df):
    """Create comprehensive Excel report"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not user_summary_df.empty:
                user_summary_df.to_excel(writer, sheet_name="User_Summary", index=False)
            if not conflicts_df.empty:
                conflicts_df.to_excel(writer, sheet_name="User_Conflicts", index=False)
            else:
                pd.DataFrame({"Message": ["No conflicts found"]}).to_excel(writer, sheet_name="User_Conflicts", index=False)
            if not user_tcodes_df.empty:
                user_tcodes_df.to_excel(writer, sheet_name="User_Role_Tcodes", index=False)
            if not function_map_df.empty:
                function_map_df.to_excel(writer, sheet_name="Function_Tcodes", index=False)
            if not risk_pairs_df.empty:
                risk_pairs_df.to_excel(writer, sheet_name="Risk_Pairs", index=False)

        output.seek(0)
        return output.read()
    except Exception as e:
        st.error(f"Error creating Excel report: {str(e)}")
        return None

# Initialize session state
if "processed_data" not in st.session_state:
    st.session_state.processed_data = {}

# Main Application
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>👤 User-Based SoD Conflict Analyzer</h1>
        <p>Upload your files to analyze Segregation of Duties conflicts</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload section
    st.markdown("## 📁 Upload Required Files")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 👥 User Data File")
        user_file = st.file_uploader(
            "Upload User Data",
            type=['csv', 'xlsx', 'xls'],
            help="File containing user information and role assignments",
            key="user_file_uploader"
        )
    
    with col2:
        st.markdown("### 🔗 Role Mapping File")
        roles_file = st.file_uploader(
            "Upload Role-Tcode Mapping",
            type=['xlsx', 'xls'],
            help="File containing role to T-code mappings",
            key="roles_file_uploader"
        )
    
    with col3:
        st.markdown("### ⚠️ Risk Configuration File")
        risk_file = st.file_uploader(
            "Upload Risk/Function Data",
            type=['xlsx', 'xls'],
            help="File containing function mappings and risk definitions",
            key="risk_file_uploader"
        )
    
    # Process files when all uploaded
    if user_file and roles_file and risk_file:
        
        if st.button("🚀 Process Files & Load Data", type="primary", use_container_width=True):
            with st.spinner("Processing uploaded files..."):
                progress_bar = st.progress(0)
                
                try:
                    # Load user data
                    progress_bar.progress(20)
                    user_data = load_user_data_from_upload(user_file)
                    if user_data is None:
                        st.stop()
                    
                    # Load role mappings
                    progress_bar.progress(40)
                    role_tcodes = load_role_tcode_mapping_from_upload(roles_file)
                    if role_tcodes is None or role_tcodes.empty:
                        st.stop()
                    
                    # Extract user roles
                    progress_bar.progress(60)
                    user_roles = load_user_role_assignments_from_upload(user_data)
                    if user_roles.empty:
                        st.error("No user-role assignments found")
                        st.stop()
                    
                    # Create user-tcode mapping
                    progress_bar.progress(70)
                    user_tcodes = create_user_tcode_mapping(user_roles, role_tcodes)
                    if user_tcodes.empty:
                        st.warning("No matching roles found between user data and role mappings")
                        st.stop()
                    
                    # Load risk data
                    progress_bar.progress(80)
                    function_map, risk_pairs = load_risk_data_from_upload(risk_file)
                    if function_map is None or risk_pairs is None:
                        st.stop()
                    
                    # Store processed data
                    progress_bar.progress(100)
                    st.session_state.processed_data = {
                        'user_data': user_data,
                        'user_roles': user_roles,
                        'role_tcodes': role_tcodes,
                        'user_tcodes': user_tcodes,
                        'function_map': function_map,
                        'risk_pairs': risk_pairs
                    }
                    
                    st.success("✅ All files processed successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")
                    st.stop()
    
    # Show analysis interface if data is processed
    if st.session_state.processed_data:
        data = st.session_state.processed_data
        
        # Show statistics
        st.markdown("---")
        st.markdown("### 📊 Data Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_users = len(data['user_tcodes']['user_id'].unique())
            st.markdown(f"""
            <div class="metric-card">
                <h2>{total_users}</h2>
                <p>Total Users</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_roles = len(data['user_tcodes']['role'].unique())
            st.markdown(f"""
            <div class="metric-card">
                <h2>{total_roles}</h2>
                <p>Total Roles</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_tcodes = len(data['user_tcodes']['tcode'].unique())
            st.markdown(f"""
            <div class="metric-card">
                <h2>{total_tcodes}</h2>
                <p>Total T-Codes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_risks = len(data['risk_pairs']['risk_id'].unique())
            st.markdown(f"""
            <div class="metric-card">
                <h2>{total_risks}</h2>
                <p>Risk Types</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Analysis tabs
        st.markdown("---")
        tab1, tab2 = st.tabs(["🔍 Individual User Analysis", "📊 Bulk Analysis & Reports"])
        
        # Individual User Analysis Tab
        with tab1:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            
            st.markdown("### 🎯 Select User to Analyze")
            
            # Show available users
            available_users = sorted(data["user_tcodes"]["user_id"].unique())
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Option 1: Dropdown selection
                user_input = st.selectbox(
                    "Choose from Available Users",
                    options=[""] + available_users,
                    help=f"Select from {len(available_users)} available users to check for conflicts",
                    key="user_selector"
                )
                
                st.markdown("**OR**")
                
                # Option 2: Manual text input
                manual_user = st.text_input(
                    "Type User ID Manually",
                    placeholder="Enter user ID...",
                    help="Type any user ID to analyze",
                    key="manual_user_input"
                )
            
            with col2:
                # Use manual input if provided, otherwise use dropdown
                final_user = manual_user.strip() if manual_user.strip() else user_input
                
                # Show quick stats for selected user
                if final_user:
                    user_data_quick = data["user_tcodes"][data["user_tcodes"]["user_id"] == final_user]
                    if not user_data_quick.empty:
                        user_name = user_data_quick["user_name"].iloc[0]
                        user_roles_list = list(user_data_quick["role"].unique())
                        user_tcodes_list = list(user_data_quick["tcode"].unique())
                        user_functions = user_data_quick.merge(data['function_map'], on='tcode', how='inner')['function_id'].unique()
                        
                        st.markdown(f"""
                        <div class="user-card">
                            <h4>👤 {user_name} ({final_user})</h4>
                            <p>• Roles: {len(user_roles_list)}</p>
                            <p>• T-Codes: {len(user_tcodes_list)}</p>
                            <p>• Functions: {len(user_functions)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='background: #fff3cd; padding: 1rem; border-radius: 8px; border-left: 4px solid #ffc107;'>
                            <h4>⚠️ User Not Found</h4>
                            <p>User ID '{final_user}' not found in uploaded data</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Automatically analyze user when selected
            if final_user and final_user != "":
                user_analysis = analyze_user_conflicts(final_user, data['user_tcodes'], data['function_map'], data['risk_pairs'])
                
                st.markdown("---")
                
                # User info header
                st.markdown(f"""
                <div class="info-card">
                    <h3>👤 User: {user_analysis.get('user_name', 'Unknown')} ({user_analysis['user_id']})</h3>
                    <p>Roles: {len(user_analysis['roles'])} | Functions: {len(user_analysis['functions'])} | T-Codes: {len(user_analysis['tcodes'])} | Conflicts: {user_analysis['conflict_count']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show error if any
                if 'error' in user_analysis:
                    st.warning(user_analysis['error'])
                else:
                    # Metrics row
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2>{len(user_analysis['roles'])}</h2>
                            <p>Roles</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2>{len(user_analysis['functions'])}</h2>
                            <p>Functions</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2>{len(user_analysis['tcodes'])}</h2>
                            <p>T-Codes</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        color = "#e74c3c" if user_analysis['conflict_count'] > 0 else "#27ae60"
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2 style="color: {color}">{user_analysis['conflict_count']}</h2>
                            <p>Conflicts</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col5:
                        status = "HIGH RISK" if user_analysis['conflict_count'] > 0 else "SAFE"
                        color = "#e74c3c" if user_analysis['conflict_count'] > 0 else "#27ae60"
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="color: {color}">{status}</h4>
                            <p>Status</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Detailed view
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("### 👔 Roles")
                        if user_analysis['roles']:
                            for role in user_analysis['roles']:
                                st.markdown(f"• `{role}`")
                        else:
                            st.info("No roles found for this user")
                    
                    with col2:
                        st.markdown("### 📋 Functions")
                        if user_analysis['functions']:
                            for func in user_analysis['functions']:
                                st.markdown(f"• `{func}`")
                        else:
                            st.info("No functions found for this user")
                    
                    with col3:
                        st.markdown("### 💻 T-Codes")
                        if user_analysis['tcodes']:
                            # Show first 10 tcodes, with option to show more
                            for tcode in user_analysis['tcodes'][:10]:
                                st.markdown(f"• `{tcode}`")
                            if len(user_analysis['tcodes']) > 10:
                                st.markdown(f"... and {len(user_analysis['tcodes']) - 10} more")
                        else:
                            st.info("No T-codes found for this user")
                    
                    # Conflicts section
                    if user_analysis['conflicts']:
                        st.markdown("### ⚠️ Detected Conflicts")
                        for i, conflict in enumerate(user_analysis['conflicts'], 1):
                            st.markdown(f"""
                            <div class="conflict-card">
                                <h4>Conflict #{i}: {conflict.get('type', 'SoD Violation')}</h4>
                                <p><strong>{conflict.get('function_1', 'N/A')}</strong> ↔️ <strong>{conflict.get('function_2', 'N/A')}</strong></p>
                                <p>{conflict.get('description', 'Segregation of Duties conflict detected')}</p>
                                <small>
                                    Roles: {conflict.get('role_1', 'N/A')} ↔️ {conflict.get('role_2', 'N/A')}<br>
                                    T-Codes: {conflict.get('tcode_1', 'N/A')} ↔️ {conflict.get('tcode_2', 'N/A')}
                                </small>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="success-card">
                            <h3>🎉 No Conflicts Found!</h3>
                            <p>This user appears to have proper segregation of duties</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Bulk Analysis Tab
        with tab2:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            
            st.markdown("### 📊 System-Wide Conflict Analysis")
            
            if st.button("🚀 Analyze All Users for Conflicts", type="primary", use_container_width=True):
                with st.spinner("🔄 Analyzing all users for conflicts..."):
                    progress_bar = st.progress(0)
                    
                    try:
                        # Analyze conflicts for all users
                        conflicts_df = analyze_conflicts(data['user_tcodes'], data['function_map'], data['risk_pairs'])
                        progress_bar.progress(100)
                        
                        st.session_state['bulk_conflicts'] = conflicts_df
                        
                    except Exception as e:
                        st.error(f"Error during bulk analysis: {str(e)}")
            
            # Show bulk analysis results
            if 'bulk_conflicts' in st.session_state:
                conflicts_df = st.session_state['bulk_conflicts']
                
                st.markdown("---")
                
                if not conflicts_df.empty:
                    # Results summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2 style="color: #e74c3c">{len(conflicts_df)}</h2>
                            <p>Total Conflicts</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        unique_users = conflicts_df['user_id'].nunique()
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2>{unique_users}</h2>
                            <p>Affected Users</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        unique_risks = conflicts_df['risk_id'].nunique()
                        st.markdown(f"""
                        <div class="metric-card">
                            <h2 style="color: #e74c3c">{unique_risks}</h2>
                            <p>Risk Types</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Show conflicts table
                    st.markdown("#### 📋 All Detected Conflicts")
                    st.dataframe(conflicts_df, use_container_width=True)
                    
                    # Create user summary
                    user_summary_df = create_user_summary(conflicts_df, data['user_tcodes'])
                    
                    if not user_summary_df.empty:
                        st.markdown("#### 👥 User Summary")
                        st.dataframe(user_summary_df, use_container_width=True)
                    
                    # Download button
                    excel_data = create_excel_report(conflicts_df, user_summary_df, data['user_tcodes'], data['function_map'], data['risk_pairs'])
                    
                    if excel_data:
                        filename = f"User_Conflict_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        
                        st.download_button(
                            label="📥 Download Complete Conflict Report (Excel)",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    # Show first 10 conflicts in detail
                    if len(conflicts_df) > 0:
                        st.markdown("#### ⚠️ Conflict Details (First 10)")
                        for i, (_, conflict) in enumerate(conflicts_df.head(10).iterrows(), 1):
                            st.markdown(f"""
                            <div class="conflict-card">
                                <h4>#{i} User: {conflict['user_name']} ({conflict['user_id']})</h4>
                                <p><strong>Risk:</strong> {conflict['risk_id']}</p>
                                <p><strong>Conflicting Functions:</strong> {conflict['function_1']} ↔️ {conflict['function_2']}</p>
                                <p><strong>Through Roles:</strong> {conflict['role_1']} ↔️ {conflict['role_2']}</p>
                                <p><strong>T-Codes:</strong> {conflict['user_tcode_f1']} ↔️ {conflict['user_tcode_f2']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if len(conflicts_df) > 10:
                            st.info(f"Showing first 10 conflicts. Total conflicts: {len(conflicts_df)}. Download the Excel report for complete details.")
                
                else:
                    st.markdown("""
                    <div class="success-card">
                        <h2>🎉 No Conflicts Found!</h2>
                        <p>All users show proper segregation of duties</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create user summary even if no conflicts
                    user_summary_df = create_user_summary(pd.DataFrame(), data['user_tcodes'])
                    
                    if not user_summary_df.empty:
                        st.markdown("#### 👥 User Summary")
                        st.dataframe(user_summary_df, use_container_width=True)
                    
                    # Download clean report
                    excel_data = create_excel_report(pd.DataFrame(), user_summary_df, data['user_tcodes'], data['function_map'], data['risk_pairs'])
                    
                    if excel_data:
                        filename = f"Clean_User_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        
                        st.download_button(
                            label="📥 Download Clean Report (Excel)",
                            data=excel_data,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Instructions when no files are uploaded
        st.markdown("---")
        st.markdown("""
        <div class="upload-area">
            <h3>📋 Getting Started</h3>
            <p>To begin analyzing SoD conflicts, please upload all three required files:</p>
            
            <h4>1. 👥 User Data File (CSV/Excel)</h4>
            <p>Should contain columns like: <code>user_id</code>, <code>user_name</code>, <code>role1</code>, <code>role2</code>, etc.</p>
            
            <h4>2. 🔗 Role Mapping File (Excel)</h4>
            <p>Should have sheets with role-to-T-code mappings</p>
            
            <h4>3. ⚠️ Risk Configuration File (Excel)</h4>
            <p>Should contain "Function T-Code Mapping" and "Risk Function Mapping" sheets</p>
            
            <p><strong>Once all files are uploaded, click "Process Files & Load Data" to begin analysis.</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin-top: 2rem;'>
        <h4>👤 User-Based SoD Conflict Analyzer</h4>
        <p>Comprehensive segregation of duties analysis for your organization</p>
        <small>Upload your files to detect potential security risks and compliance violations</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
