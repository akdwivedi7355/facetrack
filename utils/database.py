import os
import pyodbc
import base64
import cv2
import pickle
import datetime
import numpy as np
import face_recognition  # Ensure face_recognition is installed and imported

# Connection string for Windows Authentication
CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=103.12.1.132,8138;'  # Replace with your SQL Server instance name
    'DATABASE=VisiterMgmt;'  # Replace with your database name if different
    'UID=msspl;'  # Replace with your SQL Server username
    'PWD=P@$$word2024;'  # Replace with your SQL Server password
)
DB_FOLDER = 'db'

def get_connection():
    """Create and return a new database connection."""
    try:
        conn = pyodbc.connect(CONN_STR)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def create_db_folder():
    """Create the db folder if it doesn't exist."""
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
        print(f"Created folder: {DB_FOLDER}")

def get_last_visitor_id():
    """Retrieve the last visitor ID from the database and return the next ID."""
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(VisiterID) FROM VisiterInfo")
        last_id = cursor.fetchone()[0]
        return (last_id + 1) if last_id is not None else 1
    except Exception as e:
        print(f"Error retrieving last visitor ID: {e}")
        return None
    finally:
        conn.close()

def save_face_vector(visitor_id, face_vector):
    """Save the face vector to a .pkl file in the db folder."""
    create_db_folder()
    try:
        filename = os.path.join(DB_FOLDER, f"{visitor_id}.pkl")
        with open(filename, 'wb') as file:
            pickle.dump(face_vector, file)
        print(f"Face vector for visitor ID {visitor_id} saved successfully.")
    except Exception as e:
        print(f"Error saving face vector: {e}")

def register_visitor(face_vector, bitmapdata):
    """Register a new visitor by inserting details into the database, retrieving the visitor ID, and then saving the face vector to a .pkl file."""
    
    # Connect to the database
    conn = get_connection()
    if conn is None:
        return

    try:
        # Insert the visitor information into the database
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO VisiterInfo (BitMapData, UpdatedDate, FirstVisitDate)
            VALUES (?, ?, ?)
        """, (bitmapdata, datetime.datetime.now(), datetime.datetime.now()))
        conn.commit()

        # Retrieve the last inserted VisiterID
        cursor.execute("SELECT MAX(VisiterID) FROM VisiterInfo")
        visitor_id = cursor.fetchone()[0]

        if visitor_id is None:
            print("Could not retrieve the generated visitor ID.")
            return

        print(f"Visitor with ID {visitor_id} registered successfully.")

        # Save the face vector as a .pkl file
        save_face_vector(visitor_id, face_vector)

    except Exception as e:
        print(f"Error registering visitor: {e}")
    finally:
        conn.close()

def compare_faces(face_encodings):
    """Compare the given face encodings with those stored in .pkl files and return recognized IDs."""
    recognized_ids = []

    # Load all stored face encodings
    known_encodings = []
    known_ids = []

    for filename in os.listdir(DB_FOLDER):
        if filename.endswith('.pkl'):
            # Extract the numeric part of the visitor ID from the filename
            visitor_id_str = filename.split('.')[0]  # Remove the .pkl extension
            if visitor_id_str.isdigit():
                visitor_id = int(visitor_id_str)
                
                # Load the stored encoding
                with open(os.path.join(DB_FOLDER, filename), 'rb') as f:
                    stored_encoding = pickle.load(f)

                known_encodings.append(stored_encoding)
                known_ids.append(visitor_id)

    if not known_encodings:
        print("No known face encodings found.")
        return recognized_ids

    if not face_encodings:
        print("No face encodings provided.")
        return recognized_ids

    # Compare each face encoding from the image with all stored encodings
    for encoding in face_encodings:
        distances = face_recognition.face_distance(known_encodings, encoding)

        # Check if distances is empty
        if len(distances) == 0:
            print("No distances calculated.")
            continue

        # Set a threshold for matching
        threshold = 0.6
        min_distance_index = np.argmin(distances)

        if distances[min_distance_index] < threshold:
            recognized_ids.append(known_ids[min_distance_index])

    return recognized_ids

def match_face(face_vector):
    """Match the face vector with those in the .pkl files in the db folder and return the visitor ID if a match is found."""
    face_encodings = [face_vector]
    recognized_ids = compare_faces(face_encodings)
    if recognized_ids:
        return recognized_ids[0]  # Return the first recognized ID
    return None

def insert_visitor_record(visitor_id, bitmapdata):
    """Insert a new record into the VisitRecord table if no recent record exists for the same visitor ID."""
    print(f"Visitor ID: {visitor_id}, Data Type: {type(visitor_id)}")

    conn = get_connection()
    if conn is None:
        return

    try:
        cursor = conn.cursor()
        
        # Check for the most recent record for this visitor ID
        cursor.execute("""
            SELECT CheckinTime FROM VisitRecord
            WHERE VisiterID = ?
            ORDER BY CheckinTime DESC
            OFFSET 0 ROWS FETCH NEXT 1 ROW ONLY
        """, (int(visitor_id),))
        result = cursor.fetchone()
        print (result)

        # If no previous record exists, proceed to insert a new record
        if result is None:
            print(f"No previous record found for Visitor ID {visitor_id}. Inserting new record.")
            cursor.execute("""
                INSERT INTO VisitRecord (VisiterID, BitMapData, CheckinTime, RecordedDate)
                VALUES (?, ?, ?, ?)
            """, (visitor_id, bitmapdata, datetime.datetime.now(), datetime.datetime.now()))
            conn.commit()
            print(f"Visitor ID {visitor_id} record inserted successfully.")
        else:
            # Check the timestamp of the most recent record
            last_checkin_time = result[0]
            current_time = datetime.datetime.now()
            time_diff = (current_time - last_checkin_time).total_seconds()

            # Check if the last record is within the last 2 minutes (120 seconds)
            if time_diff < 120:
                print(f"Visitor ID {visitor_id} has already checked in within the last 2 minutes.")
                return

            # Insert new record if last record is older than 2 minutes
            print(f"Previous record for Visitor ID {visitor_id} is older than 2 minutes. Inserting new record.")
            cursor.execute("""
                INSERT INTO VisitRecord (VisiterID, BitMapData, CheckinTime, RecordedDate)
                VALUES (?, ?, ?, ?)
            """, (visitor_id, bitmapdata, datetime.datetime.now(), datetime.datetime.now()))
            conn.commit()
            print(f"Visitor ID {visitor_id} record inserted successfully.")
            
    except Exception as e:
        print(f"Error inserting visitor record: {e}")
    finally:
        conn.close()

def get_all_visitors():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT VisiterID, VisiterName, FirstVisitDate
        FROM VisiterInfo
    """)
    rows = cursor.fetchall()
    
    visitors = []
    for row in rows:
        visitors.append({
            'VisiterID': row[0],
            'VisiterName': row[1],
            'FirstVisitDate': row[2]
        })
    
    return visitors



def get_visitor_details(visitor_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch visitor details and bitmapdata from the database
    cursor.execute("""
        SELECT VisiterID, VisiterName, FirstVisitDate, UpdatedDate, IsCriminal, VisiterPhoto, BitMapData
        FROM VisiterInfo
        WHERE VisiterID = ?
    """, (visitor_id,))
    visitor = cursor.fetchone()

    # Fetch visit records for the visitor
    cursor.execute("""
        SELECT CheckinTime, CheckoutTime
        FROM VisitRecord
        WHERE VisiterID = ?
        ORDER BY CheckinTime DESC
    """, (visitor_id,))
    visit_records = cursor.fetchall()
    
    # Decode bitmapdata if available
    if visitor[6]:  # Assuming `bitmapdata` is at index 6
        # Decode the base64 bitmapdata
        photo_base64 = visitor[6]
        photo_data = base64.b64decode(photo_base64)
        # Convert to image format
        image = np.frombuffer(photo_data, np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        # Encode the image to base64 for HTML display
        _, buffer = cv2.imencode('.jpg', image)
        visitor_photo_base64 = base64.b64encode(buffer).decode('utf-8')
    else:
        visitor_photo_base64 = None

    visitor_data = {
        'VisiterID': visitor[0],
        'VisiterName': visitor[1],
        'FirstVisitDate': visitor[2],
        'UpdatedDate': visitor[3],
        'IsCriminal': visitor[4],
        'VisiterPhoto': visitor_photo_base64,  # Set the base64 photo data
        'VisitRecords': [
            {'CheckinTime': record[0], 'CheckoutTime': record[1]} for record in visit_records
        ]
    }
    
    return visitor_data
