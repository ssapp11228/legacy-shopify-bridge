import pandas as pd
import json
import time
import os
import random

# ==============================================================================
# 1. EXTRACTION LAYER
# ==============================================================================
def extract_inventory_data(file_path: str) -> pd.DataFrame:
    """
    Extracts data from a local legacy system CSV export.
    Validates file existence and checks for required schema columns (SKU, Quantity).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[EXTRACTION ERROR] CSV file missing: {file_path}")
    
    print(f"[1/3 EXTRACTION] Loading raw legacy CSV data from '{file_path}'...")
    df = pd.read_csv(file_path)
    
    # Schema validation
    required_columns = {'SKU', 'Quantity'}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"[EXTRACTION ERROR] Invalid schema. Missing required columns: {required_columns - set(df.columns)}")
        
    return df

# ==============================================================================
# 2. TRANSFORMATION LAYER
# ==============================================================================
def transform_data_to_shopify_payload(df: pd.DataFrame) -> list:
    """
    Transforms flat Pandas DataFrame rows into structured JSON payloads,
    matching the Shopify REST Admin API InventoryLevels specification.
    Cleans negative or invalid stock quantities.
    """
    print("[2/3 TRANSFORMATION] Normalizing schema and building JSON payloads...")
    payloads = []
    
    for _, row in df.iterrows():
        sku = str(row['SKU']).strip()
        # Quantity validation: default to 0 if missing or negative
        quantity = int(row['Quantity']) if pd.notnull(row['Quantity']) and row['Quantity'] >= 0 else 0
        
        # Shopify REST API payload structure
        payload = {
            "location_id": 90568497708,  # Target Shopify location ID
            "inventory_item": {
                "sku": sku,
                "available": quantity
            },
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        payloads.append(payload)
        
    return payloads

# ==============================================================================
# 3. DISPATCH & ERROR HANDLING LAYER
# ==============================================================================
def send_to_shopify_mock(payload: dict, max_retries: int = 3) -> bool:
    """
    Simulates sending a REST request to the Shopify Admin API.
    Includes handling for network timeouts (504 Gateway Timeout) 
    with retry logic and exponential backoff.
    """
    sku = payload["inventory_item"]["sku"]
    
    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(0.3)  # Simulate network latency
            
            # Simulate intermittent network failure / timeout (20% chance)
            if random.random() < 0.2 and attempt < max_retries:
                raise TimeoutError("504 Gateway Timeout / Shopify API Unresponsive")
                
            # Successful API response
            json_data = json.dumps(payload)
            print(f"  [HTTP 200 OK] Successfully synced SKU '{sku}' -> Payload: {json_data}")
            return True
            
        except (TimeoutError, Exception) as e:
            print(f"  [WARNING] Sync failed for SKU '{sku}' (Attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                backoff = attempt * 1.5
                print(f"  [RETRY LOGIC] Waiting {backoff:.1f}s before retrying...")
                time.sleep(backoff)
            else:
                print(f"  [CRITICAL ERROR] Max retries reached for SKU '{sku}'. Logging to dead-letter queue.")
                return False

def main():
    print("==================================================")
    print("   LEGACY TO SHOPIFY REAL-TIME INVENTORY BRIDGE   ")
    print("==================================================\n")
    
    try:
        # Step 1: Extraction
        df = extract_inventory_data("inventory.csv")
        
        # Step 2: Transformation
        payloads = transform_data_to_shopify_payload(df)
        
        # Step 3: Dispatch & Error Handling
        print(f"\n[3/3 DISPATCH] Dispatching {len(payloads)} items to Shopify API...\n")
        success_count = 0
        for payload in payloads:
            if send_to_shopify_mock(payload):
                success_count += 1
                
        print(f"\n[SUMMARY] Sync process finished: {success_count}/{len(payloads)} items synced successfully.")
        
    except Exception as err:
        print(f"\n[FATAL ERROR] Pipeline aborted: {err}")

if __name__ == "__main__":
    main()