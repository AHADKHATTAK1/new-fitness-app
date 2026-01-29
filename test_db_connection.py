import psycopg2
import sys
import os

def test_connection():
    # 1. Get URL from user input if not in env
    print("--- PostgreSQL Connection Tester ---")
    print("This script checks if a database address is valid and reachable.")
    print("\nPlease go to Render Dashboard -> PostgreSQL -> Your Database -> Copy Internal Database URL")
    print("It should look like: postgres://user:pass@dpg-xxxx-a/db_name")
    
    db_url = input("\nPaste Database URL here: ").strip()
    
    if not db_url:
        print("Error: No URL provided.")
        return

    # 2. Try to connect
    print(f"\nAttempting to connect to: {db_url.split('@')[-1] if '@' in db_url else '...'}")
    
    try:
        conn = psycopg2.connect(db_url)
        print("\n✅ SUCCESS! Connection established.")
        
        # 3. Get server version
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"Server Version: {version}")
        
        cur.close()
        conn.close()
        print("\nGood news: This URL is VALID.")
        print("ACTION: Go to Render -> Web Service -> Environment")
        print("Update DATABASE_URL with this exact value.")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ CONNECTION FAILED:")
        print(f"Error: {e}")
        print("\nPossible causes:")
        print("1. The database address is wrong/deleted.")
        print("2. You might be using 'Internal URL' from outside Render (use External URL for local test).")
        print("3. Firewall blocking connection.")

if __name__ == "__main__":
    try:
        test_connection()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    input("\nPress Enter to exit...")
