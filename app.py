import streamlit as st
import pandas as pd
from io import BytesIO
import hashlib

st.set_page_config(page_title="Excel File Comparator", layout="centered")
st.title("🔍 Excel File Comparator")
st.write("Upload two Excel files below. The app will compare them and show the rows that are missing from the smaller file.")

# Upload files
file1 = st.file_uploader("📄 Upload the larger Excel file (with full data)", type=["xlsx"])
file2 = st.file_uploader("📄 Upload the smaller Excel file (possibly missing data)", type=["xlsx"])

# Hash row helper
def hash_row(row):
    return hashlib.md5(str(row.values).encode()).hexdigest()

# Clean & prep
def clean_dataframe(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df = df.applymap(lambda x: str(x).strip().lower() if pd.notnull(x) else "")
    return df

# Convert to Excel
@st.cache_data
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

if file1 and file2:
    try:
        df_large = pd.read_excel(file1)
        df_small = pd.read_excel(file2)
    except Exception as e:
        st.error(f"❌ Error reading Excel files: {e}")
        st.stop()

    # Clean and normalize both files
    df_large_clean = clean_dataframe(df_large)
    df_small_clean = clean_dataframe(df_small)

    # Check if columns match
    if list(df_large_clean.columns) != list(df_small_clean.columns):
        st.error("❌ The columns in both files must match exactly (case-insensitive and order-sensitive).")
        st.write("📌 Columns in large file:", df_large_clean.columns.tolist())
        st.write("📌 Columns in small file:", df_small_clean.columns.tolist())
        st.stop()

    # Generate row hashes for comparison
    df_large_clean['row_hash'] = df_large_clean.apply(hash_row, axis=1)
    df_small_clean['row_hash'] = df_small_clean.apply(hash_row, axis=1)

    # Filter rows in large file that are not in small file
    missing_hashes = set(df_large_clean['row_hash']) - set(df_small_clean['row_hash'])
    missing_rows = df_large[df_large_clean['row_hash'].isin(missing_hashes)].copy()  # show original data

    # Drop hash column after use
    if 'row_hash' in df_large_clean: df_large_clean.drop('row_hash', axis=1, inplace=True)
    if 'row_hash' in df_small_clean: df_small_clean.drop('row_hash', axis=1, inplace=True)

    # Show result
    if missing_rows.empty:
        st.success("✅ No missing rows found!")
    else:
        st.success(f"✅ Found {len(missing_rows)} missing row(s).")
        st.dataframe(missing_rows)

        # Download button
        st.download_button(
            label="📥 Download missing rows as Excel",
            data=convert_df_to_excel(missing_rows),
            file_name='missing_rows.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
