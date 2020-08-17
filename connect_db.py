import psycopg2
import os
import time
from cv2 import cv2
import numpy as np
import face_recognition
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from io import BytesIO

directory = "known_people"


connection = psycopg2.connect(user = "postgres",
                                  password = "7878",
                                  host = "127.0.0.1",
                                  port = "5432",
                                  database = "face_db")

cursor = connection.cursor()

def create_table():
    create_table_query = '''CREATE TABLE user_data (
                            id SERIAL PRIMARY KEY, 
                            fullName VARCHAR(40),
                            encodings BYTEA
                            ); '''
    
    cursor.execute(create_table_query)
    connection.commit()
    print("Done")
    time.sleep(3)
    start_service()

def insert_images():
    for filename in os.listdir(directory):
        image = face_recognition.load_image_file(f"known_people/{filename}")
        encoding = face_recognition.face_encodings(image)[0]
        np_bytes = BytesIO()
        np.save(np_bytes, encoding, allow_pickle=True)
        insert_images_query = '''INSERT INTO user_data (fullName,encodings) VALUES (%s,%s);'''
        user_data = (filename[:-4],np_bytes.getvalue())
        cursor.execute(insert_images_query,user_data)
        connection.commit()
    print("Done")
    time.sleep(1)
    start_service()

def delete_table():
    delete_query = '''DROP TABLE user_data'''
    cursor.execute(delete_query)
    print("Done")
    time.sleep(1)
    start_service()

def insert_image():
    Tk().withdraw() 
    filename = askopenfilename() 
    image = face_recognition.load_image_file(filename)
    encoding = face_recognition.face_encodings(image)[0]
    insert_images_query = '''INSERT INTO user_data (fullName,encodings) VALUES (%s,%s);'''
    user_data = (input("Enter User Name :"),encoding)
    cursor.execute(insert_images_query,user_data)
    connection.commit()
    print("Done")
    time.sleep(1)
    start_service()

def compare():
    Tk().withdraw() 
    filename = askopenfilename() 
    unknown_image = face_recognition.load_image_file(filename)
    cursor.execute('''SELECT * FROM user_data''')
    data = cursor.fetchall()
    flag = 0
    for img_data in data:
        username = img_data[1]
        biden_encoding = np.load(BytesIO(img_data[3]), allow_pickle=True)
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        try:
            results = face_recognition.compare_faces([biden_encoding], unknown_encoding)
            if results[0] == True:
                print(f"user found :{username}")
                flag = 1
                break
        except:
            continue
    if flag == 0:
        print("User not found")
    time.sleep(1)
    start_service()

def video_compare():
    video_capture = cv2.VideoCapture(0)
    known_face_encodings = []
    known_face_names = []
    cursor.execute('''SELECT * FROM user_data''')
    data = cursor.fetchall()
    for img_data in data:
        known_face_encodings.append(np.load(BytesIO(img_data[2]), allow_pickle=True))
        known_face_names.append(img_data[1])
    
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        ret, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

                face_names.append(name)

        process_this_frame = not process_this_frame


    
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)


        cv2.imshow('Video', frame)


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


    video_capture.release()
    cv2.destroyAllWindows()



def start_service():
    os.system("clear")
    inp = input('''
    Enter your input:
    1. Create Table
    2. Insert Images
    3. Insert New Image
    4. Delete Table
    5. Compare Image
    6. Compare video
    7. Exit
    ''')    
    if inp == '1':
        create_table()
    elif inp == '2':
        insert_images()
    elif inp == '3':
        insert_image()
    elif inp == '4':
        delete_table()
    elif inp == '5':
        compare()
    elif inp == '6':
        video_compare()
    elif inp == '7':
        pass
    else:
        input('''Please Enter valid input : ''')



if __name__ == "__main__":
    start_service()