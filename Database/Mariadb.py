import mariadb

class MariaDB:
    def __init__(self, host, user, password, database, port=3306):
        self.db_config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port
        }
        self.conn = self.connect_db()
        if not self.conn:
            raise ConnectionError("Database connection failed. Ensure that the database is initialized correctly.")

    def connect_db(self):
        try:
            conn = mariadb.connect(**self.db_config)
            return conn
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB: {e}")
            return None

    def create_or_connect_table(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                object_name VARCHAR(255) NOT NULL,
                recognized TINYINT(1) NOT NULL CHECK (recognized IN (0,1))
            )
        """)
        self.conn.commit()

    def insert_value(self, table_name, object_name, recognized):
        cursor = self.conn.cursor()
        cursor.execute(f"INSERT INTO {table_name} (object_name, recognized) VALUES (%s, %s)", (object_name, recognized))
        self.conn.commit()

    def get_value(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        results = cursor.fetchall()
        return results

    def update_value(self, table_name, record_id, new_recognized):
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET recognized = %s WHERE id = %s", (new_recognized, record_id))
        self.conn.commit()

    def update_value_by_name(self, table_name, object_name, new_recognized):
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET recognized = %s WHERE object_name = %s", (new_recognized, object_name))
        self.conn.commit()

    def delete_value(self, table_name, record_id):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (record_id,))
        self.conn.commit()
    
    def delete_value_by_name(self, table_name, object_name):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE object_name = %s", (object_name,))
        self.conn.commit()

    def reset_database(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.conn.commit()
        print(f"Database table {table_name} reset successfully!")

    def get_all_values(self, table_name):
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        results = cursor.fetchall()
        return [item for row in results for item in row]

    def close_connection(self):
        self.conn.close()

# Example Usage:
#from NVLib.Sqlite import MariaDB

# Example Usage:
'''
#db = MariaDB(host, user, password, database, port=3306)
#db.create_or_connect_table("MyTable")

db.insert_value("detections", "Car", 1)
db.insert_value("detections", "Bike", 0)
db.insert_value("detections", "Person", 1)

print("All Recognitions:", db.get_value("detections"))

db.update_value("detections", 1, 0)
db.update_value_by_name("detections", "Bike", 1)
print("Updated Recognitions:", db.get_value("detections"))

print("All Values in a List:", db.get_all_values("detections"))

db.delete_value("detections", 2)
db.delete_value_by_name("detections", "Person")

print("After Deletions:", db.get_value("detections"))

db.reset_database("detections")
db.close_connection()
'''
