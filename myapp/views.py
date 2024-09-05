from django.http import StreamingHttpResponse
from django.shortcuts import render
import cv2
import numpy as np
import base64
from utils.database import match_face, register_visitor, insert_visitor_record,get_all_visitors,get_visitor_details
import face_recognition

# Path to the Haar cascade XML file
HAAR_CASCADE_PATH = 'utils/haarcascade_frontalface_default.xml'

def extract_face_vector(image):
    # Check image type and shape
    print("Input Image dtype:", image.dtype)
    print("Input Image shape:", image.shape)
    
    # Convert the image to RGB (face_recognition works with RGB images)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Check RGB image type and shape
    print("RGB Image dtype:", rgb_image.dtype)
    print("RGB Image shape:", rgb_image.shape)
    
    # Get the face encodings
    face_encodings = face_recognition.face_encodings(rgb_image)

    if not face_encodings:
        raise ValueError("No face found in the image")

    return face_encodings[0]

def decode_base64_image(base64_str):
    img_data = base64.b64decode(base64_str)
    np_arr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

def encode_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

def process_face_image(face_image):
    """Process the face image to either register a new visitor or recognize an existing one."""
    # Ensure the face image is in the correct format (8-bit RGB)
    if face_image.ndim != 3 or face_image.shape[2] != 3:
        raise ValueError("Input face image is not in RGB format")

    rgb_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
    
    # Get the face encodings
    try:
        face_encodings = face_recognition.face_encodings(rgb_img)
    except Exception as e:
        print(f"Error while getting face encodings: {e}")
        return None

    if not face_encodings:
        print("No faces detected in the provided image.")
        return None

    for face_vector in face_encodings:
        visitor_id = match_face(face_vector)
        
        if visitor_id is None:
            print("Face not recognized, registering new visitor.")
            register_visitor(face_vector, encode_base64(face_image))
            return None  # No ID available yet
        else:
            print(f"Visitor ID: {visitor_id}")
            insert_visitor_record(visitor_id, encode_base64(face_image))  # Record the attendance
            return visitor_id
           
def gen(camera):
    """Generate frames from the camera and display visitor ID."""
    face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
    
    while True:
        ret, frame = camera.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_image = frame[y:y+h, x:x+w]

            # Process the face image and get visitor ID
            visitor_id = process_face_image(face_image)

            # Draw rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

            # Display visitor ID
            if visitor_id:
                cv2.putText(frame, f'ID: {visitor_id}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # Encode the frame and yield it
        _, jpeg = cv2.imencode('.jpg', frame)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

camera_url = "https://192.168.1.14:8080/video"

def video_feed(request):
    return StreamingHttpResponse(gen(cv2.VideoCapture(0)),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

def index(request):
    return render(request, 'myapp/index.html')

def visitor_details(request, visitor_id):
    """Fetch and render details of a specific visitor."""
    # Get visitor details from the database
    visitor_data = get_visitor_details(visitor_id)
    
    if visitor_data:
        return render(request, 'myapp/visitor_details.html', {'visitor': visitor_data})
    else:
        return render(request, 'myapp/visitor_not_found.html', {'visitor_id': visitor_id})

def visitor_list(request):
    """Fetch and render a list of all visitors."""
    # SQL query to fetch all visitors from the VisiterInfo table
    visitors = get_all_visitors()
    
    # Pass the visitor data to the template
    return render(request, 'myapp/visitor_list.html', {'visitors': visitors})