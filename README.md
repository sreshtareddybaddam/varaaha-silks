# Varaaha Silks — V6

Premium saree storefront with FastAPI + SQLite backend.

## Features
- Product catalogue
- Shopping cart and checkout
- Customer order tracking
- Admin login/dashboard
- Add/edit/delete products
- Stock management
- Product image upload
- Order status management

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000

Admin: http://127.0.0.1:8000/admin.html
Tracking: http://127.0.0.1:8000/track.html

For production, replace the demo admin credentials, use a managed database/storage, and configure payment/WhatsApp integrations.
