
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path
import sqlite3, hashlib, secrets, json
from datetime import datetime

BASE = Path(__file__).parent
DB = BASE / "varaaha.db"
app = FastAPI(title="Varaaha Silks API", version="1.0")

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS admins(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS products(
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      category TEXT NOT NULL,
      price REAL NOT NULL,
      color TEXT,
      occasion TEXT,
      image TEXT,
      stock INTEGER DEFAULT 1,
      description TEXT
    );
    CREATE TABLE IF NOT EXISTS orders(
      id TEXT PRIMARY KEY,
      customer_name TEXT NOT NULL,
      phone TEXT NOT NULL,
      email TEXT,
      address TEXT NOT NULL,
      method TEXT NOT NULL,
      items_json TEXT NOT NULL,
      total REAL NOT NULL,
      status TEXT NOT NULL DEFAULT 'Pending',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions(
      token TEXT PRIMARY KEY,
      username TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """)
    # Demo admin: change this before deployment.
    if not conn.execute("SELECT 1 FROM admins WHERE username='admin'").fetchone():
        conn.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)",
                     ("admin", hashlib.sha256(b"change-me-123").hexdigest()))
    if conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"] == 0:
        products = [
          ("VS001","Mustard Wine Pattu Saree","Pure Pattu",3999,"Mustard & Wine","Wedding","images/saree-1.jpg",3,"A rich mustard saree with a traditional wine-toned woven border."),
          ("VS002","Magenta Rose Pattu Saree","Lightweight Pattu",3499,"Magenta & Rose","Festive","images/saree-2.jpg",4,"A vibrant magenta weave finished with an elegant rose-toned border."),
          ("VS003","Emerald Rose Pattu Saree","Wedding Collection",3999,"Emerald & Rose","Wedding","images/saree-3.jpg",2,"Deep emerald tones paired with a soft rose border for festive occasions.")
        ]
        conn.executemany("INSERT INTO products VALUES(?,?,?,?,?,?,?,?,?)", products)
    conn.commit()
    conn.close()

init_db()

class Login(BaseModel):
    username: str
    password: str

class OrderIn(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7)
    email: str = ""
    address: str = Field(min_length=5)
    method: str
    items: list[dict]

class StatusIn(BaseModel):
    status: str

def auth(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Admin login required")
    token = authorization.split(" ",1)[1]
    conn=db()
    row=conn.execute("SELECT username FROM sessions WHERE token=?", (token,)).fetchone()
    conn.close()
    if not row: raise HTTPException(401, "Invalid session")
    return row["username"]

@app.get("/api/products")
def products():
    conn=db(); rows=conn.execute("SELECT * FROM products ORDER BY id").fetchall(); conn.close()
    return [dict(r) for r in rows]

@app.post("/api/login")
def login(data: Login):
    conn=db(); row=conn.execute("SELECT password_hash FROM admins WHERE username=?", (data.username,)).fetchone()
    if not row or hashlib.sha256(data.password.encode()).hexdigest() != row["password_hash"]:
        conn.close(); raise HTTPException(401, "Invalid username or password")
    token=secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions VALUES(?,?,?)",(token,data.username,datetime.now().isoformat()))
    conn.commit(); conn.close()
    return {"token":token}

@app.post("/api/orders")
def create_order(data: OrderIn):
    conn=db()
    total=0
    clean=[]
    for item in data.items:
        row=conn.execute("SELECT * FROM products WHERE id=?", (item.get("id"),)).fetchone()
        qty=max(1,int(item.get("qty",1)))
        if not row: raise HTTPException(400, "Unknown product")
        if row["stock"] < qty: raise HTTPException(400, f"{row['name']} has only {row['stock']} left")
        total += row["price"]*qty
        clean.append({"id":row["id"],"name":row["name"],"price":row["price"],"qty":qty})
    oid="VS-"+secrets.token_hex(4).upper()
    conn.execute("""INSERT INTO orders(id,customer_name,phone,email,address,method,items_json,total,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
                 (oid,data.name,data.phone,data.email,data.address,data.method,json.dumps(clean),total,"Pending",datetime.now().isoformat()))
    for item in clean:
        conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (item["qty"],item["id"]))
    conn.commit(); conn.close()
    return {"order_id":oid,"total":total,"status":"Pending"}

@app.get("/api/admin/orders")
def admin_orders(_: str = Depends(auth)):
    conn=db(); rows=conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall(); conn.close()
    return [{**dict(r), "items":json.loads(r["items_json"])} for r in rows]

@app.get("/api/admin/stats")
def stats(_: str = Depends(auth)):
    conn=db()
    orders=conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    revenue=conn.execute("SELECT COALESCE(SUM(total),0) r FROM orders").fetchone()["r"]
    products=conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
    low=conn.execute("SELECT COUNT(*) c FROM products WHERE stock<=2").fetchone()["c"]
    conn.close()
    return {"orders":orders,"revenue":revenue,"products":products,"low_stock":low}

@app.patch("/api/admin/orders/{order_id}")
def update_status(order_id: str, data: StatusIn, _: str = Depends(auth)):
    allowed={"Pending","Confirmed","Packed","Shipped","Delivered","Cancelled"}
    if data.status not in allowed: raise HTTPException(400,"Invalid status")
    conn=db(); cur=conn.execute("UPDATE orders SET status=? WHERE id=?", (data.status,order_id))
    conn.commit(); conn.close()
    if cur.rowcount==0: raise HTTPException(404,"Order not found")
    return {"ok":True}

app.mount("/static", StaticFiles(directory=BASE/"static"), name="static")

@app.get("/")
def home(): return FileResponse(BASE/"static"/"index.html")
@app.get("/{path:path}")
def pages(path: str):
    if path.startswith("api/"): raise HTTPException(404)
    p=BASE/"static"/path
    if p.is_file(): return FileResponse(p)
    return FileResponse(BASE/"static"/"index.html")
