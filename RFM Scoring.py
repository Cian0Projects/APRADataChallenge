import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import squarify # A library for creating treemaps

# --- 1. Load the Final, Enriched Data File ---
try:
    # Load the master file created by the previous script
    df = pd.read_csv('Constituent_Master_File_With_RFM.csv')
    print("Successfully loaded Constituent_Master_File_With_RFM.csv")
except FileNotFoundError:
    print("Could not find Constituent_Master_File_With_RFM.csv. Please ensure it has been created.")
    exit()

print("\nGenerating visualizations for the final RFM segments...")

# --- 2. Visualization 1: Bar Chart of Segment Sizes ---

# Get the count of constituents in each segment and sort them
segment_counts = df['RFM_Segment'].value_counts().sort_values(ascending=False)

plt.figure(figsize=(12, 7))
sns.barplot(x=segment_counts.index, y=segment_counts.values, palette='viridis')
plt.title('Number of Constituents by Final RFM Segment', fontsize=16, fontweight='bold')
plt.xlabel('RFM Segment', fontsize=12)
plt.ylabel('Number of Constituents', fontsize=12)
plt.xticks(rotation=45, ha='right') # ha='right' aligns the labels for better readability
plt.tight_layout() # Adjust layout to make room for labels
plt.show()


# --- 3. Visualization 2: Treemap of Donor Segments ---

# First, prepare the data for the treemap
# We group by segment and calculate the size and average giving amount for each
treemap_data = df.groupby('RFM_Segment').agg(
    Monetary_Avg=('TOTAL_GIFT_AMOUNT', 'mean'),
    Size=('CONSTITUENT_ID', 'count')
).reset_index()

# For a cleaner treemap, we'll exclude the 'Non-Donors' and 'Other Donors (Date Missing)'
# to focus on the actionable donor segments.
donor_segments_for_treemap = treemap_data[
    ~treemap_data['RFM_Segment'].isin(['Non-Donor', 'Other Donors (Date Missing)'])
]


# Create the treemap visualization
plt.figure(figsize=(14, 8))
# squarify.plot sizes the rectangles by 'Size' and labels them
squarify.plot(sizes=donor_segments_for_treemap['Size'],
              # Create a label with both the segment name and its size
              label=donor_segments_for_treemap.apply(lambda x: f"{x['RFM_Segment']}\n(n={x['Size']})", axis=1),
              # Use a color palette to make the chart visually appealing
              color=sns.color_palette("coolwarm", len(donor_segments_for_treemap)),
              alpha=0.8)

plt.title('Treemap of Actionable RFM Segments', fontsize=18, fontweight='bold')
plt.axis('off') # Turn off the axes for a clean look
plt.show()

