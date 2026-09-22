import io
from pathlib import Path
import pandas as pd
import streamlit as st

# 1. Page Configuration & Custom Styling
st.set_page_config(
    page_title="DDO Pension Data Processor", page_icon="💜", layout="centered"
)

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f8f7fc;
        }
        h1, h2, h3 {
            color: #5b21b6;
            font-family: 'Inter', sans-serif;
        }
        .main-card {
            background: #ffffff;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(124, 58, 237, 0.06);
            border: 1px solid #ede9fe;
            margin-bottom: 20px;
        }
        .stButton>button {
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
            color: white;
            border-radius: 10px;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.35);
            width: 100%;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
            box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5);
            color: white;
            transform: translateY(-1px);
        }
        .footer {
            margin-top: 60px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            border-top: 1px solid #ede9fe;
            padding-top: 20px;
        }
        .footer span {
            color: #7c3aed;
            font-weight: 600;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# App Title & Description
st.title("💜 DDO Pension Data Processor")
st.markdown(
    "<p style='color: #4b5563; font-size: 16px;'>Upload your DDO spreadsheet"
    " to automatically clean data, format ID numbers, inject the DDO name, and"
    " explore interactive dashboards.</p>",
    unsafe_allow_html=True,
)

# File Uploader Container
uploaded_file = st.file_uploader(
    "📁 Choose an Excel file (.xls or .xlsx)", type=["xls", "xlsx"]
)

expected_columns = [
    'employee_id',
    'nps_id',
    'employee_name',
    'employer_contribution',
    'employee_contribution',
]

if uploaded_file is not None:
  file_size_mb = uploaded_file.size / (1024 * 1024)

  if file_size_mb > 10:
    st.error('⚠️ The uploaded file exceeds the 10 MB limit.')
  else:
    st.info(
        f'✨ Selected File: **{uploaded_file.name}** ({file_size_mb:.2f} MB)'
    )

    if st.button('🚀 Process & Analyze File', type='primary'):
      with st.spinner('✨ Cleaning data, formatting IDs, and generating sheets...'):
        try:
          ddo_name = Path(uploaded_file.name).stem

          # Read Excel file based on extension
          if uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')
          else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

          # Standardize columns
          df.columns = df.columns.astype(str).str.strip().str.lower()

          # Check columns
          missing_cols = [col for col in expected_columns if col not in df.columns]
          if missing_cols:
            st.error(f'⚠️ Missing required columns in the file: {missing_cols}')
          else:
            df = df[expected_columns]
            df = df.dropna(subset=['employee_id'])

            # Format IDs as numbers (preserving NaNs)
            for col in ['employee_id', 'nps_id']:
              df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

            df['employee_name'] = df['employee_name'].astype(str).str.strip()

            for col in ['employer_contribution', 'employee_contribution']:
              df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Insert ddo column right after employee_id
            cols = list(df.columns)
            emp_idx = cols.index('employee_id')
            cols.insert(emp_idx + 1, 'ddo')
            df['ddo'] = ddo_name
            df = df[cols]

            # Split data
            df_missing_pran = df[df['nps_id'].isna()].sort_values(
                'employee_name'
            )
            df_clean = df[df['nps_id'].notna()].sort_values('employee_name')
            duplicates = df_clean[
                df_clean.duplicated(subset=['employee_id', 'nps_id'], keep=False)
            ]

            # Trigger celebratory animation
            st.balloons()

            st.markdown('---')
            st.markdown('### 📊 Interactive Summary Dashboard')

            # Metrics row
            col1, col2, col3 = st.columns(3)
            with col1:
              st.metric(
                  label='👥 Total Scanned',
                  value=f'{len(df):,}',
                  delta='Records',
              )
            with col2:
              st.metric(
                  label='✅ Valid (MS Sheet)',
                  value=f'{len(df_clean):,}',
                  delta='Ready',
              )
            with col3:
              st.metric(
                  label='⚠️ Unposted (Missing PRAN)',
                  value=f'{len(df_missing_pran):,}',
                  delta_color='inverse',
              )

            # Contributions Visual Chart
            st.markdown('#### 💰 Total Contributions Overview')
            total_employer = df['employer_contribution'].sum()
            total_employee = df['employee_contribution'].sum()
            chart_data = pd.DataFrame(
                {
                    'Contribution Type': [
                        'Employer Contribution',
                        'Employee Contribution',
                    ],
                    'Total Amount': [total_employer, total_employee],
                }
            ).set_index('Contribution Type')
            st.bar_chart(chart_data, color='#7c3aed')

            # Interactive Search Filter for Previews
            st.markdown('#### 🔍 Live Data Explorer')
            search_query = st.text_input(
                'Type employee name or ID to search across records:'
            )

            # Apply search filter if entered
            if search_query:
              filtered_clean = df_clean[
                  df_clean['employee_name']
                  .str.contains(search_query, case=False, na=False)
                  | df_clean['employee_id'].astype(str).str.contains(search_query)
              ]
            else:
              filtered_clean = df_clean

            # Interactive Tabs for Data Preview
            tab1, tab2, tab3 = st.tabs(
                [
                    f'🟢 Valid Records ({len(df_clean)})',
                    f'🟠 Unposted ({len(df_missing_pran)})',
                    f'⚠️ Duplicates ({len(duplicates)})',
                ]
            )

            with tab1:
              if search_query:
                st.caption(
                    f'Showing search results for: "{search_query}"'
                    f' ({len(filtered_clean)} matches)'
                )
                st.dataframe(filtered_clean, use_container_width=True)
              else:
                st.dataframe(df_clean, use_container_width=True)

            with tab2:
              if not df_missing_pran.empty:
                st.dataframe(df_missing_pran, use_container_width=True)
              else:
                st.success('🎉 Zero unposted records found!')

            with tab3:
              if not duplicates.empty:
                st.dataframe(duplicates, use_container_width=True)
              else:
                st.success('🎉 Zero duplicate entries found!')

            # Write to Excel Buffer for Download
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
              df_clean.to_excel(writer, sheet_name='MS', index=False)
              df_missing_pran.to_excel(writer, sheet_name='Unposted', index=False)
              if not duplicates.empty:
                duplicates.to_excel(writer, sheet_name='Duplicates', index=False)

            output_buffer.seek(0)
            st.markdown('<br>', unsafe_allow_html=True)

            # Styled Download Button
            st.download_button(
                label=f'📥 Download Processed Workbook ({ddo_name}_Processed.xlsx)',
                data=output_buffer,
                file_name=f'{ddo_name}_Processed.xlsx',
                mime=(
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
            )

        except Exception as e:
          st.error(f'❌ An error occurred while processing the file: {e}')

# Custom Footer with your name
st.markdown(
    """
    <div class="footer">
        Designed with 💜 by <span>Amit Garhwal</span>
    </div>
""",
    unsafe_allow_html=True,
)