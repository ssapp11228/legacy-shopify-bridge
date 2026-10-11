import pandas as pd
import time
import os

def process_inventory():
    csv_file = "inventory.csv"
    if not os.path.exists(csv_file):
        print(f"[ERROR] File {csv_file} not found!")
        return

    print("=== Legacy to Sh`opify Bridge ===")
    print(f"Reading inventory data from {csv_file}...\n")
    
    # Read CSV via Pandas
    df = pd.read_csv(csv_file)
    print("Parsed Inventory Data:")
    print(df.to_string(index=False))
    
    print("\nSimulating Shopify API Synchronization...")
    for index, row in df.iterrows():
        sku = row['SKU']
        qty = row['Quantity']
        # Mocking Shopify REST API call
        print(f"[SYNC] Pushing SKU '{sku}' with Quantity: {qty} to Shopify Admin API...")
        time.sleep(0.5)
        
    print("\n[SUCCESS] Inventory sync finished successfully!")

if __name__ == "__main__":
    process_inventory()