import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def auth_table():
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS collisionavoidance(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   username TEXT UNIQUE NOT NULL,
                   email TEXT UNIQUE NOT NULL,
                   password TEXT NOT NULL
                   )''')
    conn.commit()
    conn.close()

def register_user(username,email,password):
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO collisionavoidance (username,email,password) VALUES (?,?,?)",(username,email,hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error in register_user:",e)
        conn.close()

def authenticate_user(username,password):
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM collisionavoidance WHERE username=? AND password=?",(username,hash_password(password)))
        result = cursor.fetchone()
        conn.close()
        if result == None:
            return False
        else:
            return True
    except Exception as e:
        print("Error in authenticate_user:",e)
        conn.close()

def check_username(username):
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM collisionavoidance WHERE username = ?",(username,))
        result = cursor.fetchone()
        conn.close()
        if result == None:
            return False
        else:
            return True
    except Exception as e:
        print("Error in check_username:",e)
        conn.close()

def ip_table():
    conn=sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cameras(
                   id Integer PRIMARY KEY AUTOINCREMENT,
                   ip TEXT UNIQUE NOT NULL,
                   username TEXT NOT NULL,
                   password TEXT NOT NULL
                   )''')
    conn.commit()
    conn.close()

def add_ip(username,password,ip):
    conn=sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO cameras (username,password,ip) VALUES (?,?,?)",(username,password,ip))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error in adding ip:",e)
        conn.close()
        return False

def get_cameras():
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username,password,ip FROM cameras")
        results = cursor.fetchall()
        conn.close()
        k=None
        if(results==None): k=0 
        else: k=1
        return k,results
    except Exception as e:
        print("Error in fetching cameras:",e)
        conn.close()
        return -1,[]
    
def dele():
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cameras")
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error in dele function of db.py:",e)
        conn.close()

def remove_cam(ip):
    conn = sqlite3.connect("TML_CollisionAvoidance.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cameras WHERE ip = ?",(ip,))
        conn.commit()
        conn.close()
        print(f"camera removed with ip:{ip}")
        return True
    except Exception as e:
        print("Error in removing camera:",e)
        conn.close()
        return False
