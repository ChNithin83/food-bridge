# 🌿 FoodBridge — Food Waste Redistribution App

A Flask web app that connects food donors (restaurants, hotels) with receivers (NGOs, shelters) and volunteers to reduce food waste.

---

## 🚀 Setup Instructions

### Step 1 — Install Python packages
```bash
pip install flask flask-sqlalchemy werkzeug
```

### Step 2 — Run the app
```bash
python app.py
```

### Step 3 — Open in browser
```
http://127.0.0.1:5000
```

---

## 👤 User Roles

| Role       | What they do                                      |
|------------|--------------------------------------------------|
| **Donor**      | Restaurants/hotels post surplus food         |
| **Receiver**   | NGOs/shelters browse and claim food          |
| **Volunteer**  | Pick up and deliver food, mark as delivered  |

---

## 📁 File Structure

```
food_waste_app/
├── app.py                      ← Main Flask app (routes + models)
├── requirements.txt            ← Python dependencies
├── foodwaste.db                ← SQLite database (auto-created)
└── templates/
    ├── base.html               ← Common navbar + layout
    ├── home.html               ← Landing page with stats
    ├── register.html           ← User registration
    ├── login.html              ← Login page
    ├── post_food.html          ← Donor posts food
    ├── listings.html           ← Public food listings
    ├── dashboard_donor.html    ← Donor dashboard
    ├── dashboard_receiver.html ← Receiver dashboard
    └── dashboard_volunteer.html← Volunteer dashboard
```

---

## ✅ Features Included

- User registration with 3 roles (Donor, Receiver, Volunteer)
- Secure login with hashed passwords
- Donors can post food with expiry time, quantity, address
- Receivers can browse and claim available food
- Volunteers can mark food as delivered
- Public listings page with veg/non-veg filter
- Dashboard for each role with stats
- Flash messages for user feedback
- Beautiful responsive UI with green theme

---

## 🔮 What to Add Next (Phase 2)

- [ ] Map view using Leaflet.js
- [ ] Email notifications when food is posted
- [ ] Expiry countdown timer on food cards
- [ ] Admin panel to manage all posts
- [ ] Impact stats (total meals, kg saved)
- [ ] Mobile app version

---

## 🌐 Deploy for Free

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python app.py`
6. Deploy!

---

Built with ❤️ using Flask + SQLite + Bootstrap
