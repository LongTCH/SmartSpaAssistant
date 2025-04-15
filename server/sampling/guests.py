import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
import datetime

# Load sample customers from the JSON file
import json
with open('sampling/customers.json', 'r', encoding='utf-8') as f:
    sample_customers = json.load(f)

# PostgreSQL connection parameters
db_params = {
    'database': 'smartspa',
    'user': 'root',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}


async def create_and_insert_guests():
    # Create a connection pool
    conn_str = f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"

    # Create engine
    engine = create_async_engine(conn_str)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False)

    try:
        # Create guests table if it doesn't exist
        metadata = MetaData()

        # Define the guests table
        guests = Table(
            'guests', metadata,
            Column('id', String, primary_key=True),
            Column('provider', String(50)),
            Column('account_id', String(50)),
            Column('account_name', String(100)),
            Column('avatar', Text),
            Column('fullname', String(255)),
            Column('gender', String(20)),
            Column('birthday', DateTime, default=datetime.datetime.now),
            Column('phone', String(50)),
            Column('email', String(255)),
            Column('address', Text),
            Column('last_message_at', DateTime, default=datetime.datetime.now),
            Column('last_message', JSONB),
            Column('created_at', DateTime, default=datetime.datetime.now),
            Column('message_count', Integer, default=0),
            Column('sentiment', String(50), default='neutral'),
            Column('assigned_to', String(50)),
        )

        async with engine.begin() as conn:
            # Create table if it doesn't exist
            await conn.run_sync(metadata.create_all)

        # Insert the data using raw asyncpg for better performance
        pool = await asyncpg.create_pool(**db_params)
        async with pool.acquire() as conn:
            for customer in sample_customers:
                # Convert string dates to datetime objects
                birthday = datetime.datetime.strptime(
                    customer['birthday'], '%Y-%m-%d') if customer['birthday'] else None
                last_message_at = datetime.datetime.strptime(
                    customer['last_message_at'], '%Y-%m-%d %H:%M:%S') if customer['last_message_at'] else None

                await conn.execute('''
                INSERT INTO guests (id, provider, account_id, account_name, avatar, fullname, 
                                gender, birthday, phone, email, address, last_message_at, last_message, sentiment, message_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO UPDATE SET
                    provider = EXCLUDED.provider,
                    account_id = EXCLUDED.account_id,
                    account_name = EXCLUDED.account_name,
                    avatar = EXCLUDED.avatar,
                    fullname = EXCLUDED.fullname,
                    gender = EXCLUDED.gender,
                    birthday = EXCLUDED.birthday,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email,
                    address = EXCLUDED.address,
                    last_message_at = EXCLUDED.last_message_at,
                    last_message = EXCLUDED.last_message,
                    sentiment = EXCLUDED.sentiment,
                    message_count = EXCLUDED.message_count,
                    assigned_to = EXCLUDED.assigned_to
                ''',
                                   customer['id'], customer['provider'], customer['account_id'],
                                   customer['account_name'], customer['avatar'], customer['fullname'],
                                   customer['gender'], birthday, customer['phone'],
                                   customer['email'], customer['address'], last_message_at,
                                   json.dumps({}), customer['sentiment'],
                                   customer['message_count'], customer['assigned_to'])

        print(
            f"Successfully inserted {len(sample_customers)} customers into the guests table")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close the connection pool and engine
        await engine.dispose()
        if 'pool' in locals():
            await pool.close()

# Run the async function
asyncio.run(create_and_insert_guests())
