
from psycopg import connect
from psycopg.rows import dict_row
from dataclasses import asdict, fields
from typing import Optional, Type
from .mssg import Message
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

# Load environment variables from the .env file
load_dotenv()

# DB details
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_TABLE = os.getenv("DB_TABLE")

class DBConnection:
    def __init__(
        self,
        dbname: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        table: Optional[str] = None,
    ):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.table = table

    def check_timescaledb(self):
        """Check if TimescaleDB extension is installed."""
        query = "SELECT extname FROM pg_extension WHERE extname = 'timescaledb';"
        try:
            with connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    row_factory=dict_row,
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if not result:
                        raise RuntimeError(
                            "TimescaleDB extension is not installed in the database."
                        )
        except Exception as e:
            raise RuntimeError(f"Failed to check TimescaleDB extension: {e}")

    def table_exists(self):
        """Check if a table exists in the database."""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        );
        """
        try:
            with connect(
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    row_factory=dict_row,
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (self.table,))
                    return cursor.fetchone()["exists"]
        except Exception as e:
            raise RuntimeError(f"Failed to check table existence: {e}")

    def _get_datetime_field(self, message_cls):
        """Retrieve the name of the field with datetime type."""
        for field in fields(message_cls):
            if field.type is datetime:
                return field.name
        raise ValueError("No datetime field found in the Message dataclass.")

    def create_hypertable(self,
                          message_cls: Type[Message],
                          chunk_interval: str = "7 days",
                          index_columns: Optional[list]=None):
        """Create the table and convert it to a hypertable."""
        time_column = self._get_datetime_field(message_cls)

        if not self.table_exists():
            print(f"Table '{self.table}' does not exist. Creating...")
            # Dynamically generate table schema from the Message class
            columns = [
                f"{field.name} TIMESTAMPTZ NOT NULL" if field.type is datetime
                else f"{field.name} DOUBLE PRECISION"
                for field in fields(message_cls)
            ]
            columns = ", ".join(columns)
            create_table_query = f"""
            CREATE TABLE {self.table} (
                {columns},
                PRIMARY KEY ({time_column})
            );
            """
            try:
                with connect(
                        dbname=self.dbname,
                        user=self.user,
                        password=self.password,
                        host=self.host,
                        port=self.port,
                ) as conn:
                    with conn.cursor() as cursor:
                        # Create the table
                        cursor.execute(create_table_query)
                        print(f"Table '{self.table}' created successfully.")

                        # Convert the table to a hypertable with the specified chunk interval
                        hypertable_query = f"""
                                         SELECT create_hypertable('{self.table}', '{time_column}', chunk_time_interval => INTERVAL '{chunk_interval}');
                                         """
                        cursor.execute(hypertable_query)
                        print(
                            f"Table '{self.table}' converted to a hypertable with a chunk interval of {chunk_interval}.")

                        if index_columns:
                            for column in index_columns:
                                index_query = f"CREATE INDEX IF NOT EXISTS {self.table}_{column}_idx ON {self.table} ({column});"
                                cursor.execute(index_query)
                                print(f"Secondary index on '{column}' added.")

                        conn.commit()

            except Exception as e:
                raise RuntimeError(f"Failed to create hypertable: {e}")
        else:
            print(f"Table '{self.table}' already exists.")

    def save_message(self, message: Message):
        """Insert a message into the SMARTMETER table."""
        message_dict = asdict(message)
        columns = ", ".join(message_dict.keys())
        placeholders = ", ".join(["%s"] * len(message_dict))
        query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders});"

        try:
            with connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, tuple(message_dict.values()))
                    conn.commit()
                    print(f"Message saved to table '{self.table}': {message}")
        except Exception as e:
            raise RuntimeError(f"Failed to save message: {e}")

if __name__ == "__main__":
    db = DBConnection(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        table=DB_TABLE,
    )

    db.check_timescaledb()
    db.create_hypertable(Message, index_columns=["electricity_currently_delivered"])

    # Create a sample message
    sample_message = Message(
        electricity_delivered_1=1.5,
        electricity_delivered_2=2.3,
        electricity_returned_1=0.8,
        electricity_returned_2=0.4,
        electricity_currently_delivered=0.9,
        electricity_currently_returned=0.1,
        phase_currently_delivered_l1=0.3,
        phase_currently_delivered_l2=0.3,
        phase_currently_delivered_l3=0.3,
        phase_voltage_l1=230.0,
        phase_voltage_l2=230.0,
        phase_voltage_l3=230.0,
        delivered=0.6,
        timestamp_utc=datetime.now(timezone.utc).replace(microsecond=0),
    )

    # Save the message to the database
    db.save_message(sample_message)
