import pandas as pd
from datetime import datetime

# --- Load and Prepare Data ---
try:
    df = pd.read_csv('MergedAndCleaned.csv')
    print("Successfully loaded MergedAndCleaned.csv")
except FileNotFoundError:
    print("Could not find MergedAndCleaned.csv. Please ensure it is in the same directory.")
    exit()

print("Starting RFM calculation with robust date handling...")

# --- Perform RFM Calculation ---
# Convert both potential date columns to datetime objects
df['LAST_GIFT_DATE_TRANS'] = pd.to_datetime(df['LAST_GIFT_DATE_TRANS'], errors='coerce')
df['LAST_GIFT_DATE'] = pd.to_datetime(df['LAST_GIFT_DATE'], errors='coerce')

# Create a separate DataFrame for donors to calculate scores
donors_only = df[df['TOTAL_GIFTS'] > 0].copy()

# --- *** THE ROBUST FIX *** ---
# 1. Create a consolidated final gift date by combining the two date columns.
#    It prioritizes the transaction date and falls back to the profile date.
donors_only['LAST_GIFT_DATE_FINAL'] = donors_only['LAST_GIFT_DATE_TRANS'].combine_first(donors_only['LAST_GIFT_DATE'])
print("Created a consolidated 'LAST_GIFT_DATE_FINAL' column.")

# 2. Identify constituents who are known donors but still have no final date.
missing_date_donors = donors_only[donors_only['LAST_GIFT_DATE_FINAL'].isna()]
if not missing_date_donors.empty:
    print(f"\nWarning: Found {len(missing_date_donors)} constituents with a positive gift count but no gift dates in any source file. They will not receive a Recency score.")

# 3. Drop these constituents from the scoring process to avoid errors.
donors_only.dropna(subset=['LAST_GIFT_DATE_FINAL'], inplace=True)


# Set a consistent date for Recency calculation
snapshot_date = datetime.now()
donors_only['RECENCY'] = (snapshot_date - donors_only['LAST_GIFT_DATE_FINAL']).dt.days

# Calculate R, F, and M scores using quintiles
donors_only['R_Score'] = pd.qcut(donors_only['RECENCY'], q=5, labels=[5, 4, 3, 2, 1])
donors_only['F_Score'] = pd.qcut(donors_only['TOTAL_GIFTS'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
donors_only['M_Score'] = pd.qcut(donors_only['TOTAL_GIFT_AMOUNT'], q=5, labels=[1, 2, 3, 4, 5])

# --- Merge Scores Back and Add New Columns ---

rfm_columns_to_add = ['CONSTITUENT_ID', 'R_Score', 'F_Score', 'M_Score']
df = df.merge(donors_only[rfm_columns_to_add], on='CONSTITUENT_ID', how='left')
print("\nAdded individual R, F, M score columns.")

# --- Add RFM Score Sum Column ---
df['R_Score'] = df['R_Score'].cat.add_categories([0]).fillna(0)
df['F_Score'] = df['F_Score'].cat.add_categories([0]).fillna(0)
df['M_Score'] = df['M_Score'].cat.add_categories([0]).fillna(0)
df['RFM_Score_Sum'] = df['R_Score'].astype(int) + df['F_Score'].astype(int) + df['M_Score'].astype(int)
print("Added RFM_Score_Sum column.")


# --- Add RFM Segment Label Column ---
def assign_rfm_segment(row):
    if row['TOTAL_GIFTS'] == 0:
        return 'Non-Donor'
    
    # If R_Score is 0, it means the date was missing. Classify as 'Other Donors'.
    if row['R_Score'] == 0:
        return 'Other Donors'

    r_score, f_score, m_score = row['R_Score'], row['F_Score'], row['M_Score']
    
    if r_score >= 4 and f_score >= 4 and m_score >= 4:
        return 'Champions'
    elif r_score >= 4 and f_score >= 4:
        return 'Potential Loyalists'
    elif f_score >= 4:
        return 'Loyalists'
    elif r_score >= 4:
        return 'Recent Donors'
    elif m_score >= 4:
        return 'High Value Donors'
    elif r_score <= 2:
        return 'At-Risk / Lapsed'
    else:
        return 'Other Donors'

df['RFM_Segment'] = df.apply(assign_rfm_segment, axis=1)
print("Added RFM_Segment label column.")


# --- Save the Enriched DataFrame to a New CSV File ---
output_filename = 'Constituent_Data_With_RFM_Final.csv'
df.to_csv(output_filename, index=False)

print(f"\nProcessing complete!")
print(f"A new file named '{output_filename}' has been created with all the final RFM data.")

