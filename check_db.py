import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def check_table():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("MISSING_CREDS")
        return

    supabase = create_client(url, key)
    try:
        supabase.table("workspaces").select("*").limit(1).execute()
        print("EXISTS")
    except Exception as e:
        if "relation \"public.workspaces\" does not exist" in str(e):
            print("NOT_EXISTS")
        else:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    check_table()
