import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import squarify

# --- Load and Prepare Data ---
try:
    df = pd.read_csv('MergedAndCleaned.csv')
    print("Successfully loaded MergedAndCleaned.csv")
except FileNotFoundError:
    print("Could not find MergedAndCleaned.csv")
    exit()

# --- Perform RFM Calculation ---
df['LAST_GIFT_DATE_TRANS'] = pd.to_datetime(df['LAST_GIFT_DATE_TRANS'], errors='coerce')
donors_only = df[df['TOTAL_GIFTS'] > 0].copy()

snapshot_date = datetime.now()
donors_only['RECENCY'] = (snapshot_date - donors_only['LAST_GIFT_DATE_TRANS']).dt.days
donors_only['R_Score'] = pd.qcut(donors_only['RECENCY'], q=5, labels=[5, 4, 3, 2, 1])
donors_only['F_Score'] = pd.qcut(donors_only['TOTAL_GIFTS'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
donors_only['M_Score'] = pd.qcut(donors_only['TOTAL_GIFT_AMOUNT'], q=5, labels=[1, 2, 3, 4, 5])
donors_only['RFM_Score'] = donors_only['R_Score'].astype(str) + donors_only['F_Score'].astype(str) + donors_only['M_Score'].astype(str)

rfm_columns = ['CONSTITUENT_ID', 'R_Score', 'F_Score', 'M_Score', 'RFM_Score']
df = df.merge(donors_only[rfm_columns], on='CONSTITUENT_ID', how='left')


# --- *** NEW AND IMPROVED SEGMENTATION FUNCTION *** ---

def assign_rfm_segment(rfm_score):
    if pd.isna(rfm_score):
        return 'Non-Donors'

    # The new hierarchical logic ensures each constituent gets one unique label.
    if rfm_score == '555':
        return 'Champions (555)'
    elif rfm_score[1] == '5' and rfm_score[0] == '5': # F=5 and R=5
        return 'New Loyalists (55X)'
    elif rfm_score[1] == '5': # Any other F=5
        return 'Loyalists (X5X)'
    elif rfm_score[0] == '5': # Any other R=5
        return 'Recent Donors (5XX)'
    elif rfm_score[2] == '5': # Any other M=5
        return 'High Value Donors (XX5)'
    elif rfm_score[0] in ['1', '2']:
        return 'At-Risk / Lapsed (1XX, 2XX)'
    else:
        return 'Other Donors'

df['RFM_Segment'] = df['RFM_Score'].apply(assign_rfm_segment)

# --- Visualizations (Code is the same, but will now use the new labels) ---

print("\n--- Analysis Complete with Improved Segments. Generating Visuals ---")

segment_counts = df['RFM_Segment'].value_counts().sort_values(ascending=False)

plt.figure(figsize=(12, 7))
sns.barplot(x=segment_counts.index, y=segment_counts.values, palette='viridis')
plt.title('Number of Constituents by RFM Segment', fontsize=16, fontweight='bold')
plt.xlabel('RFM Segment', fontsize=12)
plt.ylabel('Number of Constituents', fontsize=12)
plt.xticks(rotation=45, ha='right') # ha='right' aligns the labels better
plt.tight_layout() # Adjust layout to make room for labels
plt.show()

# Treemap
treemap_data = df.groupby('RFM_Segment').agg(
    Monetary_Avg=('TOTAL_GIFT_AMOUNT', 'mean'),
    Size=('CONSTITUENT_ID', 'count')
).reset_index()

treemap_data = treemap_data[treemap_data['RFM_Segment'] != 'Non-Donors']

plt.figure(figsize=(14, 8))
squarify.plot(sizes=treemap_data['Size'],
              label=treemap_data.apply(lambda x: f"{x['RFM_Segment']}\n(n={x['Size']})", axis=1),
              color=sns.color_palette("coolwarm", len(treemap_data)),
              alpha=0.8)
plt.title('RFM Segments Treemap', fontsize=18, fontweight='bold')
plt.axis('off')
plt.show()