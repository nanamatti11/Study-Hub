--  SELECT * FROM students;



-- INSERT INTO students(username,password)
-- --  VALUES ('Sam',12345678);
-- INSERT INTO instructors(username,password,fullname,email,subject)
-- VALUES('sam@cobe.gmail.com','mypassword','Otoo Gray','instructor1@gmail.com','Mathematics');

-- -- SELECT * FROM students;

-- ALTER TABLE students ADD COLUMN fullname TEXT;
-- ALTER TABLE students ADD COLUMN email TEXT;

-- ALTER TABLE instructors ADD COLUMN subject TEXT;

-- cursor.execute('''CREATE TABLE IF NOT EXISTS students (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT UNIQUE NOT NULL,
--     fullname TEXT NOT NULL,
--     email TEXT UNIQUE NOT NULL,
--     password TEXT NOT NULL
-- )''')
-- cursor.execute('''CREATE TABLE IF NOT EXISTS instructors (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT UNIQUE NOT NULL,
--     fullname TEXT NOT NULL,
--     email TEXT UNIQUE NOT NULL,
--     password TEXT NOT NULL,
--     subject TEXT NOT NULL
-- )''')

--  INSERT INTO students(username,password,fullname,email)
--  VALUES('sam@cobe.gmail.com','mypassword','Otoo Gray','instructor1@gmail.com');

SELECT * FROM students;