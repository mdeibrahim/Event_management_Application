import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL server
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='123',
    host='localhost',
    port='5432'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Create a cursor
cur = conn.cursor()

# Terminate all connections to the database
cur.execute("""
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'ems_db'
    AND pid <> pg_backend_pid()
""")

# Drop the database if it exists
cur.execute("DROP DATABASE IF EXISTS ems_db")

# Create a new database
cur.execute("CREATE DATABASE ems_db")

# Close the cursor and connection
cur.close()
conn.close()

print("Database reset complete!") 