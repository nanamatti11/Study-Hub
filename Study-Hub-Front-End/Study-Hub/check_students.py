import sqlite3

def check_students():
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    
    print("Available Student Login Credentials:")
    print("=" * 50)
    
    cursor.execute('SELECT username, email, fullname FROM students')
    students = cursor.fetchall()
    
    if not students:
        print("No students found in database!")
    else:
        for student in students:
            print(f"Username: {student[0]}")
            print(f"Email: {student[1]}")
            print(f"Full Name: {student[2]}")
            print("-" * 30)
    
    print(f"\nTotal students: {len(students)}")
    
    # Also check instructors
    print("\nAvailable Instructor Login Credentials:")
    print("=" * 50)
    
    cursor.execute('SELECT username, email, fullname, subject FROM instructors')
    instructors = cursor.fetchall()
    
    if not instructors:
        print("No instructors found in database!")
    else:
        for instructor in instructors:
            print(f"Username: {instructor[0]}")
            print(f"Email: {instructor[1]}")
            print(f"Full Name: {instructor[2]}")
            print(f"Subject: {instructor[3]}")
            print("-" * 30)
    
    print(f"\nTotal instructors: {len(instructors)}")
    
    conn.close()

if __name__ == "__main__":
    check_students()
