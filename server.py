import mysql.connector
from mysql.connector import Error
from datetime import datetime

def manage_numberplate_db(numberplate):
    """Process detected number plates, verify bookings, and return status messages."""
    host = "localhost"
    user = "root"
    password = ""
    database = "numberplate"
    port = 3306

    connection = None
    try:
        # Connect to MySQL Server
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database
        )
        if connection.is_connected():
            cursor = connection.cursor()
             # Ensure `numberplate` table exists
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS numberplate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numberplate VARCHAR(50),
                entry_date DATE,
                entry_time TIME
            )
            """)
            
            # Insert detected number plate into `numberplate` table
            insert_data_query = """
            INSERT INTO numberplate (numberplate, entry_date, entry_time)
            VALUES (%s, %s, %s)
            """
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            cursor.execute(insert_data_query, (numberplate, current_date, current_time))
            connection.commit()  # Commit the transaction


            # Ensure required tables exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookingslist (
                booking_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                vehicle_plate_no VARCHAR(50) UNIQUE
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS verified_plates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                numberplate VARCHAR(50) UNIQUE,
                entry_date DATE,
                entry_time TIME
            )
            """)

            current_date = datetime.now().date()
            current_time = datetime.now().time()

            # Clean and validate number plate
            numberplate = numberplate.strip().upper()
            if not numberplate:
                return "Standing By"

            # Check if the detected plate is in `bookingslist`
            check_query = "SELECT * FROM bookingslist WHERE vehicle_plate_no = %s"
            cursor.execute(check_query, (numberplate,))
            booking = cursor.fetchone()

            if booking:
                # Insert into `verified_plates`
                verified_query = """
                INSERT INTO verified_plates (numberplate, entry_date, entry_time)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE entry_date = VALUES(entry_date), entry_time = VALUES(entry_time)
                """
                cursor.execute(verified_query, (numberplate, current_date, current_time))
                connection.commit()
                return "Gateway Open!"
            else:
                return "Unknown Vehicle!"

    except Error as e:
        print(f"Database Error: {e}")
        return "DB Error"
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
