from services.database import supabase

print("Starting Supabase test...")

try:
    response = supabase.table("issues").select("*").limit(1).execute()

    print("✅ Successfully connected to Supabase!")
    print("Issues table is accessible.")
    print("Response:", response)

except Exception as e:
    print("❌ Connection failed!")
    print(e)