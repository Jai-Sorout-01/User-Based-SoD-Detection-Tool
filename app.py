import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
from typing import Dict, List, Tuple, Any
import time
import base64

# Page config
st.set_page_config(
    page_title="Victora - User-Based SoD Conflict Analyzer", 
    page_icon="👤", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

def load_logo():
    """Load and encode the company logo"""
    try:
        with open("Victora logo.svg", "r", encoding="utf-8") as f:
            svg_content = f.read()
        # Encode SVG for embedding
        b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{b64_svg}"
    except FileNotFoundError:
        # Fallback if logo file is not found
        return None

def get_logo_html(logo_data):
    """Generate HTML for logo display"""
    if logo_data:
        return f"""
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
            <img src="{logo_data}" style="height: 80px; margin-right: 20px;" alt="Victora Logo"/>
        </div>
        """
    else:
        return """
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1rem;">
            <div style="height: 80px; width: 200px; background: linear-gradient(45deg, #667eea, #764ba2); 
                        border-radius: 10px; display: flex; align-items: center; justify-content: center; 
                        color: white; font-size: 24px; font-weight: bold; margin-right: 20px;">
                VICTORA
            </div>
        </div>
        """

# Load company logo
logo_data = load_logo()

# Enhanced Custom CSS for attractive styling with company branding
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    /* Company Header */
    .company-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .company-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .company-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .company-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        font-weight: 400;
        opacity: 0.95;
        position: relative;
        z-index: 1;
    }
    
    .company-branding {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 1;
    }
    
    .company-branding img {
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
    }
    
    /* Enhanced Cards */
    .conflict-card {
        background: linear-gradient(135deg, #ff6b6b, #ee5a24);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 0.8rem 0;
        box-shadow: 0 8px 25px rgba(238, 90, 36, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .conflict-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(238, 90, 36, 0.4);
    }
    
    .success-card {
        background: linear-gradient(135deg, #00b894, #00cec9);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0, 184, 148, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
        margin: 1rem 0;
    }
    
    .info-card {
        background: linear-gradient(135deg, #6c5ce7, #a29bfe);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 0.8rem 0;
        box-shadow: 0 8px 25px rgba(108, 92, 231, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .user-card {
        background: linear-gradient(135deg, #fd79a8, #e84393);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 0.8rem 0;
        box-shadow: 0 8px 25px rgba(253, 121, 168, 0.3);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        border: 1px solid rgba(102, 126, 234, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.15);
    }
    
    .metric-card h2 {
        margin: 0 0 0.5rem 0;
        font-size: 2.2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .metric-card h4 {
        margin: 0 0 0.5rem 0;
        font-size: 1.4rem;
        font-weight: 600;
    }
    
    .metric-card p {
        margin: 0;
        color: #6c757d;
        font-weight: 500;
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2.5rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* File Upload Area */
    .upload-section {
        background: linear-gradient(135deg, #f8f9ff, #e8f0fe);
        border: 2px dashed #667eea;
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        margin: 1.5rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #f0f4ff, #e0ecfe);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.1);
    }
    
    .upload-area {
        background: linear-gradient(135deg, #f9fbfd, #ffffff);
        border: 2px dashed #4a90e2;
        border-radius: 20px;
        padding: 2.5rem;
        text-align: left;
        font-family: 'Inter', sans-serif;
        color: #333;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        margin: 2rem 0;
    }
    
    .upload-area h3 {
        color: #2c3e50;
        font-size: 1.8rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .upload-area h4 {
        margin-top: 1.5rem;
        font-size: 1.3rem;
        color: #34495e;
        font-weight: 500;
    }
    
    .upload-area p {
        font-size: 1rem;
        margin: 0.8rem 0;
        line-height: 1.6;
        color: #5a6c7d;
    }
    
    .upload-area code {
        background: linear-gradient(135deg, #eef2f7, #f8fafc);
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 0.9rem;
        color: #667eea;
        border: 1px solid #e1e8ed;
    }
    
    .upload-area strong {
        color: #e74c3c;
        font-weight: 600;
    }
    
    /* Tab Content */
    .tab-content {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        margin-top: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Progress Bar Styling */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea, #764ba2);
    }
    
    /* Footer Styling */
    .company-footer {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-top: 3rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .company-footer h4 {
        margin: 0 0 0.5rem 0;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .company-footer p {
        margin: 0.5rem 0;
        opacity: 0.9;
    }
    
    .company-footer small {
        opacity: 0.8;
        font-size: 0.9rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .company-header h1 {
            font-size: 2rem;
        }
        
        .company-header p {
            font-size: 1rem;
        }
        
        .metric-card {
            padding: 1.5rem;
        }
        
        .tab-content {
            padding: 1.5rem;
        }
    }
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
                "total_tcodes
