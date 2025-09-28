# Database Table Viewer for Personal Expense Tracker
from app import app, db
from sqlalchemy import inspect, text

def view_all_tables():
    with app.app_context():
        inspector = inspect(db.engine)
        
        print("=" * 60)
        print("DATABASE TABLES IN YOUR EXPENSE TRACKER")
        print("=" * 60)
        
        # Get all table names
        tables = inspector.get_table_names()
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print(f"\nFound {len(tables)} tables:")
        print("-" * 40)
        
        for i, table in enumerate(tables, 1):
            print(f"{i}. {table}")
        
        print("\n" + "=" * 60)
        print("DETAILED TABLE INFORMATION")
        print("=" * 60)
        
        # Get detailed information about each table
        for table_name in tables:
            print(f"\n--- TABLE: {table_name.upper()} ---")
            
            # Get column information
            columns = inspector.get_columns(table_name)
            print("Columns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" (default: {col['default']})" if col['default'] is not None else ""
                print(f"  • {col['name']}: {col['type']} {nullable}{default}")
            
            # Get row count
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"Rows: {count}")
            except Exception as e:
                print(f"Could not get row count: {e}")
            
            print("-" * 50)
        
        print("\n" + "=" * 60)
        print("SAMPLE DATA FROM EACH TABLE")
        print("=" * 60)
        
        # Show sample data from each table
        for table_name in tables:
            try:
                result = db.session.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                rows = result.fetchall()
                
                if rows:
                    print(f"\n--- SAMPLE DATA FROM {table_name.upper()} ---")
                    for i, row in enumerate(rows, 1):
                        print(f"Row {i}: {dict(row._mapping)}")
                else:
                    print(f"\n--- {table_name.upper()} is empty ---")
                    
            except Exception as e:
                print(f"\n--- Could not read from {table_name}: {e} ---")
            
            print("-" * 50)

if __name__ == "__main__":
    print("Starting database inspection...")
    try:
        view_all_tables()
        print("\nDatabase inspection completed successfully!")
    except Exception as e:
        print(f"Error during database inspection: {e}")
        print("Make sure your Flask app is properly configured and the database exists.")
