import pandas as pd
from datetime import datetime

# --- 1. Load the Main Data and the Reliable Gift Summary ---
try:
    df_main = pd.read_csv('MergedAndCleaned.csv')
    print("Successfully loaded MergedAndCleaned.csv")
except FileNotFoundError:
    print("Could not find MergedAndCleaned.csv. Please ensure it is in the same directory.")
    exit()

try:
    df_gift_summary = pd.read_csv('Comprehensive_Gift_Summary.csv')
    print("Successfully loaded Comprehensive_Gift_Summary.csv")
except FileNotFoundError:
    print("Could not find Comprehensive_Gift_Summary.csv. Please ensure it has been created by the previous script.")
    exit()

# --- 2. Merge and Update with Reliable Data ---
print("\nMerging reliable gift summary into the main dataset...")

# Rename summary columns for clarity during the merge
df_gift_summary.rename(columns={
    'TOTAL_GIFTS': 'RELIABLE_TOTAL_GIFTS',
    'MOST_RECENT_GIFT': 'RELIABLE_LAST_GIFT_DATE',
    'FIRST_GIFT': 'RELIABLE_FIRST_GIFT_DATE'
}, inplace=True)

# Perform a left merge to bring the reliable data into the main dataframe
df_final = pd.merge(df_main, df_gift_summary, on='CONSTITUENT_ID', how='left')

# Convert all date columns to datetime
df_final['LAST_GIFT_DATE'] = pd.to_datetime(df_final['LAST_GIFT_DATE'], errors='coerce')
df_final['FIRST_GIFT_DATE'] = pd.to_datetime(df_final['FIRST_GIFT_DATE'], errors='coerce')
df_final['RELIABLE_LAST_GIFT_DATE'] = pd.to_datetime(df_final['RELIABLE_LAST_GIFT_DATE'], errors='coerce')
df_final['RELIABLE_FIRST_GIFT_DATE'] = pd.to_datetime(df_final['RELIABLE_FIRST_GIFT_DATE'], errors='coerce')


# Update the main columns with the reliable data where it exists
# The .combine_first() method fills in missing values in one series from another.
df_final['LAST_GIFT_DATE'] = df_final['RELIABLE_LAST_GIFT_DATE'].combine_first(df_final['LAST_GIFT_DATE'])
df_final['FIRST_GIFT_DATE'] = df_final['RELIABLE_FIRST_GIFT_DATE'].combine_first(df_final['FIRST_GIFT_DATE'])
# For gift counts, we directly replace the old value if a new reliable one exists.
df_final['TOTAL_GIFTS'] = df_final['RELIABLE_TOTAL_GIFTS'].fillna(df_final['TOTAL_GIFTS'])

# Drop the temporary reliable columns
df_final.drop(columns=['RELIABLE_TOTAL_GIFTS', 'RELIABLE_LAST_GIFT_DATE', 'RELIABLE_FIRST_GIFT_DATE'], inplace=True)
print("Updated gift counts and dates with the more reliable data.")


# --- 3. Proceed with Final RFM Calculation on Corrected Data ---
print("\nStarting final RFM calculation...")

donors_only = df_final[df_final['TOTAL_GIFTS'] > 0].copy()
donors_only.dropna(subset=['LAST_GIFT_DATE'], inplace=True)

snapshot_date = datetime.now()
donors_only['RECENCY'] = (snapshot_date - donors_only['LAST_GIFT_DATE']).dt.days

donors_only['R_Score'] = pd.qcut(donors_only['RECENCY'], q=5, labels=[5, 4, 3, 2, 1])
donors_only['F_Score'] = pd.qcut(donors_only['TOTAL_GIFTS'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
donors_only['M_Score'] = pd.qcut(donors_only['TOTAL_GIFT_AMOUNT'], q=5, labels=[1, 2, 3, 4, 5])

rfm_columns_to_add = ['CONSTITUENT_ID', 'R_Score', 'F_Score', 'M_Score']
df_final = df_final.merge(donors_only[rfm_columns_to_add], on='CONSTITUENT_ID', how='left')

df_final['R_Score'] = df_final['R_Score'].cat.add_categories([0]).fillna(0)
df_final['F_Score'] = df_final['F_Score'].cat.add_categories([0]).fillna(0)
df_final['M_Score'] = df_final['M_Score'].cat.add_categories([0]).fillna(0)
df_final['RFM_Score_Sum'] = df_final['R_Score'].astype(int) + df_final['F_Score'].astype(int) + df_final['M_Score'].astype(int)

def assign_rfm_segment(row):
    if row['TOTAL_GIFTS'] == 0:
        return 'Non-Donor'
    if row['R_Score'] == 0:
        return 'Other Donors (Date Missing)'

    r_score, f_score, m_score = row['R_Score'], row['F_Score'], row['M_Score']
    if r_score >= 4 and f_score >= 4 and m_score >= 4: return 'Champions'
    elif r_score >= 4 and f_score >= 4: return 'Potential Loyalists'
    elif f_score >= 4: return 'Loyalists'
    elif r_score >= 4: return 'Recent Donors'
    elif m_score >= 4: return 'High Value Donors'
    elif r_score <= 2: return 'At-Risk / Lapsed'
    else: return 'Other Donors'

df_final['RFM_Segment'] = df_final.apply(assign_rfm_segment, axis=1)
print("Final segmentation complete.")


# --- 4. Save the Final, Master Enriched File ---
output_filename = 'Constituent_Master_File_With_RFM.csv'
df_final.to_csv(output_filename, index=False)

print(f"\nProcessing complete!")
print(f"A new master file named '{output_filename}' has been created with corrected data and final RFM segments.")
