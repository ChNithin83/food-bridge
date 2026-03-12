from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

app = Flask(__name__)
app.secret_key = 'food_waste_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foodwaste.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ─────────────────────────────────────────
# EMAIL CONFIGURATION
# ─────────────────────────────────────────
EMAIL_ADDRESS = 'your_gmail@gmail.com'      # ← Change this to your Gmail
EMAIL_PASSWORD = 'your_app_password_here'   # ← Change this (Gmail App Password)

db = SQLAlchemy(app)

# ─────────────────────────────────────────
# DATABASE MODELS
# ─────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # donor / receiver / volunteer
    organization = db.Column(db.String(150))
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FoodPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    food_type = db.Column(db.String(50))
    expiry_time = db.Column(db.DateTime, nullable=False)
    pickup_address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='available')
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    donor = db.relationship('User', backref='food_posts')

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_post_id = db.Column(db.Integer, db.ForeignKey('food_post.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    volunteer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    claimed_at = db.Column(db.DateTime, default=datetime.utcnow)
    delivered_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='claimed')
    food_post = db.relationship('FoodPost', backref='claims')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='claims')
    volunteer = db.relationship('User', foreign_keys=[volunteer_id], backref='deliveries')

# ─────────────────────────────────────────
# EMAIL FUNCTIONS
# ─────────────────────────────────────────

def send_email(to_email, subject, html_body):
    """Send a single HTML email via Gmail SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'FoodBridge 🌿 <{EMAIL_ADDRESS}>'
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        print(f'✅ Email sent to {to_email}')
    except Exception as e:
        print(f'❌ Email failed to {to_email}: {e}')


def notify_receivers_new_food(post, donor):
    """Email ALL receivers when new food is posted"""
    receivers = User.query.filter_by(role='receiver').all()
    if not receivers:
        return

    subject = f'🍱 New Food Available: {post.food_name} — FoodBridge'
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f7faf8;padding:20px;border-radius:16px;">
      <div style="background:linear-gradient(135deg,#1a7a4a,#0f5c35);padding:30px;border-radius:12px;text-align:center;color:white;margin-bottom:20px;">
        <div style="font-size:3rem;">🌿</div>
        <h1 style="margin:10px 0 5px;font-size:1.6rem;">New Food Available!</h1>
        <p style="opacity:0.9;margin:0;">Act fast before it expires!</p>
      </div>

      <div style="background:white;border-radius:12px;padding:24px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
        <h2 style="color:#1a7a4a;margin-top:0;">🍽️ {post.food_name}</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px 0;color:#666;width:130px;">📦 Quantity</td><td style="padding:8px 0;font-weight:600;">{post.quantity}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">🌱 Type</td><td style="padding:8px 0;font-weight:600;">{'Vegetarian' if post.food_type == 'veg' else 'Non-Vegetarian'}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📍 Pickup</td><td style="padding:8px 0;font-weight:600;">{post.pickup_address}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">⏰ Expires</td><td style="padding:8px 0;font-weight:600;color:#e74c3c;">{post.expiry_time.strftime('%d %b %Y, %I:%M %p')}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">🏪 Donor</td><td style="padding:8px 0;font-weight:600;">{donor.organization or donor.name}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📞 Phone</td><td style="padding:8px 0;font-weight:600;">{donor.phone or 'Not provided'}</td></tr>
          {'<tr><td style="padding:8px 0;color:#666;">📝 Notes</td><td style="padding:8px 0;">' + post.notes + '</td></tr>' if post.notes else ''}
        </table>
      </div>

      <div style="text-align:center;margin:24px 0;">
        <a href="http://127.0.0.1:5000/dashboard"
           style="background:#1a7a4a;color:white;padding:14px 36px;border-radius:50px;text-decoration:none;font-weight:700;font-size:1rem;display:inline-block;">
          🙌 Claim This Food Now
        </a>
      </div>

      <p style="text-align:center;color:#999;font-size:0.82rem;">
        Claim quickly — food expires soon!<br>
        <strong style="color:#1a7a4a;">FoodBridge</strong> — Reducing waste, feeding lives 🌿
      </p>
    </div>
    """

    for receiver in receivers:
        t = threading.Thread(target=send_email, args=(receiver.email, subject, html_body))
        t.daemon = True
        t.start()


def notify_donor_food_claimed(post, receiver, donor):
    """Email donor when their food is claimed by an NGO"""
    subject = '✅ Your food donation was claimed! — FoodBridge'
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f7faf8;padding:20px;border-radius:16px;">
      <div style="background:linear-gradient(135deg,#e67e22,#d35400);padding:30px;border-radius:12px;text-align:center;color:white;margin-bottom:20px;">
        <div style="font-size:3rem;">🎉</div>
        <h1 style="margin:10px 0 5px;font-size:1.6rem;">Your Food Was Claimed!</h1>
        <p style="opacity:0.9;margin:0;">An NGO is coming to collect it</p>
      </div>

      <div style="background:white;border-radius:12px;padding:24px;margin-bottom:16px;">
        <h2 style="color:#e67e22;margin-top:0;">🍽️ {post.food_name}</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:8px 0;color:#666;width:140px;">🏛️ Claimed By</td><td style="padding:8px 0;font-weight:600;">{receiver.organization or receiver.name}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📞 Their Phone</td><td style="padding:8px 0;font-weight:600;">{receiver.phone or 'Not provided'}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📧 Their Email</td><td style="padding:8px 0;font-weight:600;">{receiver.email}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">🕐 Claimed At</td><td style="padding:8px 0;">{datetime.utcnow().strftime('%d %b %Y, %I:%M %p')}</td></tr>
        </table>
        <div style="background:#fef3e2;border-radius:8px;padding:12px;margin-top:16px;color:#e67e22;font-size:0.9rem;">
          <strong>📋 Next Step:</strong> Please keep the food ready for pickup. A volunteer will contact you soon.
        </div>
      </div>

      <p style="text-align:center;color:#999;font-size:0.82rem;">
        Thank you for your generosity! 🙏<br>
        <strong style="color:#1a7a4a;">FoodBridge</strong> — Reducing waste, feeding lives 🌿
      </p>
    </div>
    """
    t = threading.Thread(target=send_email, args=(donor.email, subject, html_body))
    t.daemon = True
    t.start()


def notify_volunteers_pickup_needed(post, receiver):
    """Email ALL volunteers when food is claimed and needs pickup"""
    volunteers = User.query.filter_by(role='volunteer').all()
    if not volunteers:
        return

    subject = f'🚴 Pickup Needed! {post.food_name} — FoodBridge'
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f7faf8;padding:20px;border-radius:16px;">
      <div style="background:linear-gradient(135deg,#8e44ad,#6c3483);padding:30px;border-radius:12px;text-align:center;color:white;margin-bottom:20px;">
        <div style="font-size:3rem;">🚴</div>
        <h1 style="margin:10px 0 5px;font-size:1.6rem;">Pickup Needed!</h1>
        <p style="opacity:0.9;margin:0;">Someone needs a volunteer to deliver food</p>
      </div>

      <div style="background:white;border-radius:12px;padding:24px;margin-bottom:16px;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
        <h2 style="color:#8e44ad;margin-top:0;">🍽️ {post.food_name}</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr style="background:#f8f0ff;"><td colspan="2" style="padding:10px;font-weight:700;color:#6c3483;border-radius:6px;">📦 PICKUP FROM</td></tr>
          <tr><td style="padding:8px 0;color:#666;width:140px;">🏪 Donor</td><td style="padding:8px 0;font-weight:600;">{post.donor.organization or post.donor.name}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📍 Address</td><td style="padding:8px 0;font-weight:600;">{post.pickup_address}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📞 Phone</td><td style="padding:8px 0;font-weight:600;">{post.donor.phone or 'Not provided'}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📦 Quantity</td><td style="padding:8px 0;font-weight:600;">{post.quantity}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">⏰ Expires</td><td style="padding:8px 0;font-weight:600;color:#e74c3c;">{post.expiry_time.strftime('%d %b %Y, %I:%M %p')}</td></tr>

          <tr style="background:#e8f5ee;"><td colspan="2" style="padding:10px;font-weight:700;color:#1a7a4a;border-radius:6px;">🏛️ DELIVER TO</td></tr>
          <tr><td style="padding:8px 0;color:#666;">🏛️ NGO</td><td style="padding:8px 0;font-weight:600;">{receiver.organization or receiver.name}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📍 Address</td><td style="padding:8px 0;font-weight:600;">{receiver.address or 'See app for details'}</td></tr>
          <tr><td style="padding:8px 0;color:#666;">📞 Phone</td><td style="padding:8px 0;font-weight:600;">{receiver.phone or 'Not provided'}</td></tr>
        </table>
      </div>

      <div style="text-align:center;margin:24px 0;">
        <a href="http://127.0.0.1:5000/dashboard"
           style="background:#8e44ad;color:white;padding:14px 36px;border-radius:50px;text-decoration:none;font-weight:700;font-size:1rem;display:inline-block;">
          🚴 I'll Deliver This!
        </a>
      </div>

      <p style="text-align:center;color:#999;font-size:0.82rem;">
        First volunteer to accept gets the delivery!<br>
        <strong style="color:#1a7a4a;">FoodBridge</strong> — Reducing waste, feeding lives 🌿
      </p>
    </div>
    """

    for volunteer in volunteers:
        t = threading.Thread(target=send_email, args=(volunteer.email, subject, html_body))
        t.daemon = True
        t.start()


def notify_delivery_complete(post, receiver, donor):
    """Email both donor and receiver when food is successfully delivered"""
    subject = '🚀 Food Delivered Successfully! — FoodBridge'

    for recipient_email, recipient_name in [
        (donor.email, donor.organization or donor.name),
        (receiver.email, receiver.organization or receiver.name)
    ]:
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f7faf8;padding:20px;border-radius:16px;">
          <div style="background:linear-gradient(135deg,#1a7a4a,#27ae60);padding:30px;border-radius:12px;text-align:center;color:white;margin-bottom:20px;">
            <div style="font-size:3rem;">✅</div>
            <h1 style="margin:10px 0 5px;font-size:1.6rem;">Food Delivered!</h1>
            <p style="opacity:0.9;margin:0;">Mission accomplished 🙏</p>
          </div>
          <div style="background:white;border-radius:12px;padding:24px;text-align:center;">
            <p style="font-size:1.05rem;color:#333;line-height:1.6;">
              <strong>{post.food_name}</strong> ({post.quantity}) was successfully
              delivered to <strong>{receiver.organization or receiver.name}</strong>.
            </p>
            <p style="color:#666;font-size:0.92rem;">
              Thank you <strong>{donor.organization or donor.name}</strong> for donating! 💚<br>
              Together we're fighting hunger one meal at a time.
            </p>
          </div>
          <p style="text-align:center;color:#999;font-size:0.82rem;margin-top:20px;">
            <strong style="color:#1a7a4a;">FoodBridge</strong> — Reducing waste, feeding lives 🌿
          </p>
        </div>
        """
        t = threading.Thread(target=send_email, args=(recipient_email, subject, html_body))
        t.daemon = True
        t.start()

# ─────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

# ─────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────

@app.route('/')
def home():
    stats = {
        'total_donations': FoodPost.query.count(),
        'available': FoodPost.query.filter_by(status='available').count(),
        'delivered': FoodPost.query.filter_by(status='delivered').count(),
        'donors': User.query.filter_by(role='donor').count(),
    }
    recent = FoodPost.query.filter_by(status='available').order_by(FoodPost.posted_at.desc()).limit(6).all()
    return render_template('home.html', stats=stats, recent=recent, user=get_current_user())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        organization = request.form.get('organization', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_pw,
                    role=role, organization=organization, phone=phone, address=address)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', user=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_role'] = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', user=None)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

# ─────────────────────────────────────────
# ROUTES — DASHBOARD
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    if user.role == 'donor':
        posts = FoodPost.query.filter_by(donor_id=user.id).order_by(FoodPost.posted_at.desc()).all()
        return render_template('dashboard_donor.html', user=user, posts=posts)
    elif user.role == 'receiver':
        available = FoodPost.query.filter_by(status='available').order_by(FoodPost.posted_at.desc()).all()
        my_claims = Claim.query.filter_by(receiver_id=user.id).all()
        return render_template('dashboard_receiver.html', user=user, available=available, my_claims=my_claims)
    elif user.role == 'volunteer':
        # All claimed posts that need a volunteer
        claimed_posts = FoodPost.query.filter_by(status='claimed').all()

        # My active deliveries (I accepted but not delivered yet)
        my_deliveries = Claim.query.filter_by(
            volunteer_id=user.id, status='claimed'
        ).all()

        # My completed deliveries
        completed = Claim.query.filter_by(
            volunteer_id=user.id, status='delivered'
        ).all()

        return render_template('dashboard_volunteer.html',
            user=user,
            claimed_posts=claimed_posts,
            my_deliveries=my_deliveries,
            completed=completed
        )

# ─────────────────────────────────────────
# ROUTES — FOOD POSTS
# ─────────────────────────────────────────

@app.route('/post-food', methods=['GET', 'POST'])
@login_required
def post_food():
    user = get_current_user()
    if user.role != 'donor':
        flash('Only donors can post food.', 'warning')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        food_name = request.form['food_name']
        quantity = request.form['quantity']
        food_type = request.form['food_type']
        expiry_str = request.form['expiry_time']
        pickup_address = request.form['pickup_address']
        notes = request.form.get('notes', '')

        expiry_time = datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M')

        post = FoodPost(
            donor_id=user.id,
            food_name=food_name,
            quantity=quantity,
            food_type=food_type,
            expiry_time=expiry_time,
            pickup_address=pickup_address,
            notes=notes
        )
        db.session.add(post)
        db.session.commit()

        # 📧 Notify all receivers
        notify_receivers_new_food(post, user)

        flash('Food posted! All NGOs have been notified by email. 📧', 'success')
        return redirect(url_for('dashboard'))

    return render_template('post_food.html', user=user)

@app.route('/claim/<int:post_id>', methods=['POST'])
@login_required
def claim_food(post_id):
    user = get_current_user()
    if user.role != 'receiver':
        flash('Only receivers can claim food.', 'warning')
        return redirect(url_for('dashboard'))

    post = FoodPost.query.get_or_404(post_id)
    if post.status != 'available':
        flash('This food has already been claimed.', 'warning')
        return redirect(url_for('dashboard'))

    post.status = 'claimed'
    claim = Claim(food_post_id=post.id, receiver_id=user.id)
    db.session.add(claim)
    db.session.commit()

    # 📧 Notify donor
    notify_donor_food_claimed(post, user, post.donor)

    # 📧 Notify all volunteers
    notify_volunteers_pickup_needed(post, user)

    flash('Food claimed! Donor and all volunteers have been notified by email. 📧', 'success')
    return redirect(url_for('dashboard'))

@app.route('/mark-delivered/<int:post_id>', methods=['POST'])
@login_required
def mark_delivered(post_id):
    post = FoodPost.query.get_or_404(post_id)
    post.status = 'delivered'
    if post.claims:
        post.claims[0].delivered_at = datetime.utcnow()
        post.claims[0].status = 'delivered'
    db.session.commit()

    # 📧 Notify both donor and receiver
    if post.claims:
        notify_delivery_complete(post, post.claims[0].receiver, post.donor)

    flash('Marked as delivered! Both donor and receiver notified. 📧', 'success')
    return redirect(url_for('dashboard'))

@app.route('/accept-delivery/<int:post_id>', methods=['POST'])
@login_required
def accept_delivery(post_id):
    user = get_current_user()
    if user.role != 'volunteer':
        flash('Only volunteers can accept deliveries.', 'warning')
        return redirect(url_for('dashboard'))

    post = FoodPost.query.get_or_404(post_id)
    if post.status != 'claimed':
        flash('This delivery has already been accepted or is not available.', 'warning')
        return redirect(url_for('dashboard'))

    # Assign volunteer to the claim
    if post.claims:
        claim = post.claims[0]
        if claim.volunteer_id:
            flash('Another volunteer already accepted this delivery!', 'warning')
            return redirect(url_for('dashboard'))
        claim.volunteer_id = user.id
        db.session.commit()
        flash(f'You accepted the delivery! Pick up from {post.pickup_address} 🚴', 'success')
    return redirect(url_for('dashboard'))


@app.route('/listings')
def listings():
    food_type = request.args.get('type', '')
    query = FoodPost.query.filter_by(status='available')
    if food_type:
        query = query.filter_by(food_type=food_type)
    posts = query.order_by(FoodPost.posted_at.desc()).all()
    return render_template('listings.html', posts=posts, user=get_current_user(), food_type=food_type)

# ─────────────────────────────────────────
# ROUTES — MAP
# ─────────────────────────────────────────

def geocode_address(address):
    """Convert address to lat/lng using OpenStreetMap Nominatim (free)"""
    try:
        import urllib.request
        import urllib.parse
        import json
        query = urllib.parse.urlencode({'q': address + ', India', 'format': 'json', 'limit': 1})
        url = f'https://nominatim.openstreetmap.org/search?{query}'
        req = urllib.request.Request(url, headers={'User-Agent': 'FoodBridge/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f'Geocoding failed for {address}: {e}')
    return None, None

@app.route('/map')
def food_map():
    import json
    posts = FoodPost.query.filter(FoodPost.status != 'delivered').order_by(FoodPost.posted_at.desc()).all()

    food_json = []
    for post in posts:
        # Try to geocode the address
        lat, lng = geocode_address(post.pickup_address)

        # Fallback: use Tirupati center + small random offset so pins don't overlap
        if not lat:
            import random
            lat = 13.6288 + random.uniform(-0.03, 0.03)
            lng = 79.4192 + random.uniform(-0.03, 0.03)

        food_json.append({
            'id': post.id,
            'food_name': post.food_name,
            'quantity': post.quantity,
            'food_type': post.food_type,
            'status': post.status,
            'address': post.pickup_address,
            'expiry': post.expiry_time.strftime('%d %b, %I:%M %p'),
            'donor': post.donor.organization or post.donor.name,
            'phone': post.donor.phone or '',
            'lat': lat,
            'lng': lng,
        })

    return render_template('map.html',
        posts=posts,
        food_json=json.dumps(food_json),
        user=get_current_user()
    )

# ─────────────────────────────────────────
# INIT DB & RUN
# ─────────────────────────────────────────

# Create tables always (needed for Render)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("✅ Database created!")
    print("🚀 Running at http://127.0.0.1:5000")
    app.run(debug=True)