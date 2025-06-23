# Option Chain Data Collector

**Just enter the credentials in the `config.py` file and run the `main.py` file. That's all you need to do!**

A robust system for collecting and storing NIFTY, BANKNIFTY, and other option chain data in real-time using PostgreSQL AWS RDS.

## Features

- Automatic data collection during market hours ((09:15:00 AM to 3:30:00 PM)
- Handles multiple symbols: NIFTY, BANKNIFTY, SENSEX, RELIANCE, KOTAKBANK, INFY
- Automatic weekend and holiday handling
- Robust error handling and recovery
- Detailed logging system
- PostgreSQL AWS RDS database storage
- Automatic timing management
- Hierarchical database structure

## Prerequisites

- Python 3.8+
- PostgreSQL AWS RDS database
- Dhan Trading API credentials

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd option-chain-collector
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env` file:
```
# Dhan Trading API Credentials
DHAN_CLIENT_CODE=your_dhan_client_code_here
DHAN_TOKEN_ID=your_dhan_token_id_here

# PostgreSQL AWS RDS Database Configuration
DB_HOST=your_aws_rds_endpoint.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_username
DB_PASSWORD=your_database_password
```

## Database Structure

The system creates a hierarchical database structure for storing option chain data:

### Schema Hierarchy
```
option_chain (main schema)
├── option_chain_nifty
├── option_chain_banknifty
├── option_chain_sensex
├── option_chain_reliance
├── option_chain_kotakbank
└── option_chain_infy
```

### Table Structure
Each symbol has tables named as `{symbol}_{expiry_date}` containing:
- All option chain data columns (CE/PE OI, Volume, IV, LTP, Greeks, etc.)
- Symbol, expiry_date, fetch_time, timestamp
- Automatic created_at timestamp

## Usage

### Basic Run
```bash
python main.py
```

### Run as Background Process
```bash
nohup python main.py > output.log 2>&1 &
```

### Run as System Service (Linux)
1. Create service file:
```bash
sudo nano /etc/systemd/system/option-chain.service
```

2. Add service configuration:
```ini
[Unit]
Description=Option Chain Data Collector
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/your/script
ExecStart=/usr/bin/python3 /path/to/your/script/main.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

3. Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start option-chain
sudo systemctl enable option-chain
```

## Data Collection

- Starts automatically at 7:34:00 AM
- Collects data every minute
- Stores data in PostgreSQL AWS RDS database
- Handles market hours automatically
- Skips weekends and holidays
- Creates tables automatically for each symbol/expiry combination

## Database Queries

### Using the Query Utility
```python
from query_data import get_latest_data, get_today_data, get_data_by_date_range

# Get latest data for NIFTY
df = get_latest_data('NIFTY', num_records=100)

# Get today's data for BANKNIFTY
df = get_today_data('BANKNIFTY')

# Get data for specific date range
df = get_data_by_date_range('NIFTY', '2024-01-01', '2024-01-31')
```

### Direct SQL Queries
```sql
-- Get latest data for NIFTY
SELECT * FROM option_chain_nifty.nifty_25_jan_2024 
ORDER BY fetch_time DESC, timestamp DESC 
LIMIT 100;

-- Get data for specific time range
SELECT * FROM option_chain_banknifty.banknifty_25_jan_2024 
WHERE fetch_time BETWEEN '2024-01-25 09:15:00' AND '2024-01-25 15:30:00'
ORDER BY fetch_time DESC;

-- Get all available symbols
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name LIKE 'option_chain_%';
```

## Monitoring

- Check logs in `option_chain.log`
- Monitor system service status:
```bash
sudo systemctl status option-chain
```
- View service logs:
```bash
sudo journalctl -u option-chain -f
```

## Error Handling

- Automatic retry on errors
- Detailed error logging
- Graceful shutdown handling
- Database connection recovery
- Automatic table creation for new expiries

## Configuration

Edit `config.py` to modify:
- Market hours
- Collection interval
- Symbols and their parameters
- Number of expiries and strikes

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the repository or contact the maintainers.

## Note

The rate limit applicable for Option Chain API is at 1 request per 3 second. This is because OI data gets updated slow, compared to LTP or other data parameter.
