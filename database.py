import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

# Create SQLAlchemy engine
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_connection():
    """Get a direct psycopg2 connection"""
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        raise

def get_db_session():
    """Get SQLAlchemy session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        logging.error(f"Error creating database session: {str(e)}")
        raise

def create_tables():
    """Create all necessary tables for option chain data"""
    try:
        # Create base schema for option chain data
        with engine.connect() as conn:
            # Create schema for option_chain if it doesn't exist
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS option_chain"))
            
            # Create individual symbol schemas (this is what we actually use)
            symbols = ['nifty', 'banknifty', 'sensex', 'reliance', 'kotakbank', 'infy']
            for symbol in symbols:
                schema_name = f"option_chain_{symbol}"
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            
            conn.commit()
        
        logging.info("Database schemas created successfully")
        
    except Exception as e:
        logging.error(f"Error creating database tables: {str(e)}")
        raise

def create_symbol_table(symbol, expiry_date):
    """Create table for a specific symbol and expiry date"""
    try:
        table_name = f"{symbol}_{expiry_date.replace(' ', '_').replace('-', '_')}"
        
        # Create table with exact same structure as CSV
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS option_chain_{symbol}.{table_name} (
            id SERIAL PRIMARY KEY,
            "Symbol" VARCHAR(20),
            "expiry_date" VARCHAR(50),
            "fetch_time" TIMESTAMP,
            "Spot Price" FLOAT,
            "ATM Strike" FLOAT,
            "CE OI" BIGINT,
            "CE Chg in OI" BIGINT,
            "CE Volume" BIGINT,
            "CE IV" FLOAT,
            "CE LTP" FLOAT,
            "CE Bid Qty" BIGINT,
            "CE Bid" FLOAT,
            "CE Ask" FLOAT,
            "CE Ask Qty" BIGINT,
            "CE Delta" FLOAT,
            "CE Theta" FLOAT,
            "CE Gamma" FLOAT,
            "CE Vega" FLOAT,
            "Strike Price" FLOAT,
            "PE Bid Qty" BIGINT,
            "PE Bid" FLOAT,
            "PE Ask" FLOAT,
            "PE Ask Qty" BIGINT,
            "PE LTP" FLOAT,
            "PE IV" FLOAT,
            "PE Volume" BIGINT,
            "PE Chg in OI" BIGINT,
            "PE OI" BIGINT,
            "PE Delta" FLOAT,
            "PE Theta" FLOAT,
            "PE Gamma" FLOAT,
            "PE Vega" FLOAT,
            "timestamp" VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        
        logging.info(f"Table {table_name} created successfully in schema option_chain_{symbol}")
        return table_name
        
    except Exception as e:
        logging.error(f"Error creating table for {symbol}_{expiry_date}: {str(e)}")
        raise

def insert_option_chain_data(symbol, expiry_date, df):
    """Insert option chain data into PostgreSQL table"""
    try:
        table_name = create_symbol_table(symbol, expiry_date)
        
        # Insert data using SQLAlchemy
        with engine.connect() as conn:
            # Convert DataFrame to list of dictionaries for insertion
            df_dict = df.to_dict('records')
            
            # Insert data using executemany for better performance
            insert_sql = f"""
            INSERT INTO option_chain_{symbol}.{table_name} (
                "Symbol", "expiry_date", "fetch_time", "Spot Price", "ATM Strike",
                "CE OI", "CE Chg in OI", "CE Volume", "CE IV", "CE LTP",
                "CE Bid Qty", "CE Bid", "CE Ask", "CE Ask Qty",
                "CE Delta", "CE Theta", "CE Gamma", "CE Vega",
                "Strike Price",
                "PE Bid Qty", "PE Bid", "PE Ask", "PE Ask Qty",
                "PE LTP", "PE IV", "PE Volume", "PE Chg in OI", "PE OI",
                "PE Delta", "PE Theta", "PE Gamma", "PE Vega",
                "timestamp"
            ) VALUES (
                %(Symbol)s, %(expiry_date)s, %(fetch_time)s, %(Spot Price)s, %(ATM Strike)s,
                %(CE OI)s, %(CE Chg in OI)s, %(CE Volume)s, %(CE IV)s, %(CE LTP)s,
                %(CE Bid Qty)s, %(CE Bid)s, %(CE Ask)s, %(CE Ask Qty)s,
                %(CE Delta)s, %(CE Theta)s, %(CE Gamma)s, %(CE Vega)s,
                %(Strike Price)s,
                %(PE Bid Qty)s, %(PE Bid)s, %(PE Ask)s, %(PE Ask Qty)s,
                %(PE LTP)s, %(PE IV)s, %(PE Volume)s, %(PE Chg in OI)s, %(PE OI)s,
                %(PE Delta)s, %(PE Theta)s, %(PE Gamma)s, %(PE Vega)s,
                %(timestamp)s
            )
            """
            
            # Execute batch insert using psycopg2 for better performance
            with get_db_connection() as pg_conn:
                with pg_conn.cursor() as cursor:
                    cursor.executemany(insert_sql, df_dict)
                pg_conn.commit()
        
        logging.info(f"Successfully inserted {len(df)} records into {table_name}")
        return len(df)
        
    except Exception as e:
        logging.error(f"Error inserting data for {symbol}_{expiry_date}: {str(e)}")
        raise

def test_database_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logging.info("Database connection successful")
            return True
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}")
        return False 
