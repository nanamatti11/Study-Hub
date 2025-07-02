import sqlite3

def check_database():
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    
    print("=== Students ===")
    cursor.execute('SELECT username, email, fullname FROM students')
    students = cursor.fetchall()
    for student in students:
        print(f"Username: {student[0]}, Email: {student[1]}, Fullname: {student[2]}")
    
    print("\n=== Instructors ===")
    cursor.execute('SELECT username, email, fullname, subject FROM instructors')
    instructors = cursor.fetchall()
    for instructor in instructors:
        print(f"Username: {instructor[0]}, Email: {instructor[1]}, Fullname: {instructor[2]}, Subject: {instructor[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_database() 