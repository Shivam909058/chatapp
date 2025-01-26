from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_KEY")
)

def test_connection():
    try:
        # Try to fetch a single record from messages
        response = supabase.table('messages').select("*").limit(1).execute()
        print("✅ Successfully connected to Supabase!")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the connection when running this file directly
    test_connection() 