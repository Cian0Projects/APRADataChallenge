import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import squarify
import matplotlib.colors as mcolors

# --- 1. Define Your Final Segmentation Logic ---
# This function assigns a unique segment to each donor based on their RFM scores.
def assign_rfm_segment(row):
    # Check for non-donors or donors with missing dates first
    if row['TOTAL_GIFTS'] == 0:
        return 'Non-Donor'
    if row['R_Score'] == 0:
        return 'Other Donors (Date Missing)'

    # Get the individual scores
    r_score, f_score, m_score = row['R_Score'], row['F_Score'], row['M_Score']

    # Apply hierarchical logic to assign the single best segment
    if r_score >= 4 and f_score >= 4 and m_score >= 4:
        return 'Champions'
    elif r_score >= 4 and f_score >= 4:
        return 'Active Loyalists'  # Using the improved name
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

# --- 2. Load the Final Master Data File ---
try:
    # Ensure this filename exactly matches the one in your folder
    df = pd.read_excel('Constituent_Master_File_With_RFM_and_BANDS.xlsx')
    print("Successfully loaded Constituent_Master_File_With_RFM_and_BANDS.xlsx")
except FileNotFoundError:
    print("\n--- ERROR ---")
    print("Could not find the file 'Constituent_Master_File_With_RFM_and_BANDS.xlsx'.")
    print("Please make sure the Excel file is in the same folder as your Python script and the name is spelled correctly.")
    exit() # Stop the script if the file isn't found

# --- 3. Apply Segmentation and Get Accurate Counts ---
print("\nApplying final RFM segmentation...")
df['RFM_Segment'] = df.apply(assign_rfm_segment, axis=1)

print("Segmentation complete. Counting constituents in each segment...")
segment_counts = df['RFM_Segment'].value_counts()

print("\n--- Final RFM Segment Counts ---")
print(segment_counts)
print("---------------------------------")


# --- 4. Generate the Treemap Visualization ---
print("\nGenerating final treemap visualization...")

# Define the logical order of your actionable segments from 'best' to 'worst'
ordered_actionable_segments = [
    'Champions',
    'Active Loyalists',
    'Loyalists',
    'Recent Donors',
    'High Value Donors',
    'Other Donors',
    'At-Risk / Lapsed'
]

# Create a colormap from green to red
cmap = plt.cm.get_cmap('GnYlRd') # Green to Red (no _r needed)
segment_colors_map = {}
for i, segment in enumerate(ordered_actionable_segments):
    norm_val = i / (len(ordered_actionable_segments) - 1)
    segment_colors_map[segment] = mcolors.to_hex(cmap(norm_val))

# Prepare data for treemap
treemap_data = df.groupby('RFM_Segment').agg(
    Size=('CONSTITUENT_ID', 'count')
).reset_index()

# Filter for the actionable donor segments and maintain the custom order
final_treemap_data = treemap_data[
    treemap_data['RFM_Segment'].isin(ordered_actionable_segments)
].set_index('RFM_Segment').loc[ordered_actionable_segments].reset_index()

# Get the colors for the segments in the final treemap data
treemap_segment_colors = [segment_colors_map.get(segment, '#cccccc') for segment in final_treemap_data['RFM_Segment']]

# Plot the treemap
plt.figure(figsize=(16, 9))
squarify.plot(sizes=final_treemap_data['Size'],
              label=final_treemap_data.apply(lambda x: f"{x['RFM_Segment']}\n(n={int(x['Size'])})", axis=1),
              color=treemap_segment_colors,
              alpha=0.9,
              text_kwargs={'fontsize':12, 'weight':'bold'})

plt.title('Treemap of Actionable RFM Segments: Green (Best) to Red (Worst)', fontsize=20, fontweight='bold')
plt.axis('off')
plt.show()
