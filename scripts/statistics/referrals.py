import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Load the data from a CSV file
# Replace 'orders.csv' with your actual file path and ensure the delimiter is correct
df = pd.read_csv('statistics/referrals.csv', delimiter=';')

# Function to clean the referrer URLs
def clean_referrer(url):
    if isinstance(url, str):
        # Remove the protocol (http:// or https://) and www.
        url = re.sub(r'^https?:\/\/(www\.)?', '', url)
        # Extract the domain name
        domain = url.split('/')[0]
        return domain
    return 'Unknown'  # Handle non-string values


# Apply the cleaning function
df['CLEAN_REFERRER'] = df['REFERRER'].apply(clean_referrer)

# Count the occurrences of each unique referrer
referrer_counts = df['CLEAN_REFERRER'].value_counts()

# Plotting
plt.figure(figsize=(12, 7))
sns.barplot(x=referrer_counts.index, y=referrer_counts.values, palette="deep")
plt.xlabel('Referrer', fontsize=14)
plt.ylabel('Number of Orders', fontsize=14)
plt.title('Orders by Referrer', fontsize=16)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Show plot
plt.show()
