# Varaaha Silks — Version 4

A real backend prototype for the Varaaha Silks online store.

## Stack
- Python + FastAPI
- SQLite
- HTML/CSS/JavaScript
- Local image storage

## Run on your Mac
1. Open Terminal in this folder.
2. Create a virtual environment:
   `python3 -m venv .venv`
3. Activate it:
   `source .venv/bin/activate`
4. Install dependencies:
   `pip install -r requirements.txt`
5. Start the server:
   `uvicorn main:app --reload`
6. Open:
   `http://127.0.0.1:8000`

## Admin
Open `/admin.html`

Demo credentials:
- Username: `admin`
- Password: `change-me-123`

IMPORTANT: change the demo password and secret/authentication setup before putting the site on the public internet.

## Current functionality
- Real API product catalogue
- Cart
- Checkout
- Orders saved to SQLite
- Stock decreases when an order is placed
- Admin login/session
- Admin order dashboard
- Revenue and low-stock stats
- Order status updates

## Not yet connected
- Production payment gateway
- Real shipping provider
- Production email/SMS/WhatsApp automation
- Cloud database
- Production authentication hardening
