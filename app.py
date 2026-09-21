import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from models import db, User, Room, Message
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-key-change-me')
app.config['JSON_AS_ASCII'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ============================================
# FILE UPLOAD CONFIGURATION
# ============================================
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024   # 50 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'ico'}
ALLOWED_AUDIO_EXT = {'mp3', 'wav', 'ogg', 'm4a', 'webm', 'aac', 'flac', 'opus'}
ALLOWED_VIDEO_EXT = {'mp4', 'webm', 'mov', 'avi', 'mkv', 'm4v', 'flv', 'wmv', '3gp'}
ALLOWED_DOCUMENT_EXT = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'rtf', 'odt', 'ods', 'odp',
    'zip', 'rar', '7z', 'tar', 'gz',
    'json', 'xml', 'html', 'css', 'js', 'py', 'md'
}

db.init_app(app)
bcrypt = Bcrypt(app)

with app.app_context():
    db.create_all()
    print("✅ Chat App database created successfully!")


# ============================================
# DECORATORS
# ============================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# HELPER FUNCTIONS
# ============================================
def get_media_type(filename):
    """Determine media type from file extension."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext in ALLOWED_IMAGE_EXT:
        return 'image'
    elif ext in ALLOWED_AUDIO_EXT:
        return 'audio'
    elif ext in ALLOWED_VIDEO_EXT:
        return 'video'
    elif ext in ALLOWED_DOCUMENT_EXT:
        return 'document'
    return None


def serialize_message(m):
    """Convert a Message to a JSON-serializable dict."""
    return {
        'id': m.id,
        'content': m.content or '',
        'username': m.author.username,
        'user_id': m.user_id,
        'created_at': m.created_at.strftime('%I:%M %p'),
        'media_type': m.media_type,
        'media_url': url_for('uploaded_file', filename=m.media_filename) if m.media_filename else None,
        'media_original_name': m.media_original_name,
        'media_size': m.media_size,
    }


# ============================================
# HOME ROUTE
# ============================================
@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('index.html', rooms=None)

    rooms = Room.query.order_by(Room.created_at.desc()).all()
    return render_template('index.html', rooms=rooms)


# ============================================
# AUTHENTICATION ROUTES
# ============================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        elif User.query.filter_by(username=username).first():
            errors.append('This username is already taken')

        if not email or '@' not in email or '.' not in email:
            errors.append('Please enter a valid email')
        elif User.query.filter_by(email=email).first():
            errors.append('This email is already registered')

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters')

        if password != confirm_password:
            errors.append('Passwords do not match')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html', username=username, email=email)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True

            user.last_seen = datetime.now()
            db.session.commit()

            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/rooms')
@login_required
def rooms():
    all_rooms = Room.query.order_by(Room.created_at.desc()).all()
    return render_template('rooms.html', rooms=all_rooms)


# ============================================
# ROOM ROUTES
# ============================================
@app.route('/room/new', methods=['GET', 'POST'])
@login_required
def new_room():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Room name is required', 'error')
            return render_template('new_room.html', name=name, description=description)

        if len(name) < 3:
            flash('Room name must be at least 3 characters', 'error')
            return render_template('new_room.html', name=name, description=description)

        if Room.query.filter_by(name=name).first():
            flash('A room with this name already exists', 'error')
            return render_template('new_room.html', name=name, description=description)

        room = Room(
            name=name,
            description=description,
            creator_id=session['user_id']
        )
        db.session.add(room)
        db.session.commit()

        flash(f'Room "{name}" created!', 'success')
        return redirect(url_for('view_room', room_id=room.id))

    return render_template('new_room.html')


@app.route('/room/<int:room_id>')
@login_required
def view_room(room_id):
    room = Room.query.get_or_404(room_id)
    messages = Message.query.filter_by(room_id=room_id).order_by(
        Message.created_at.asc()
    ).all()
    return render_template('view_room.html', room=room, messages=messages)


# ============================================
# TEXT MESSAGE
# ============================================
@app.route('/room/<int:room_id>/send', methods=['POST'])
@login_required
def send_message(room_id):
    room = Room.query.get_or_404(room_id)

    if request.is_json:
        data = request.get_json()
        content = data.get('content', '').strip()
    else:
        content = request.form.get('content', '').strip()

    if not content:
        response = jsonify({'error': 'Message cannot be empty'})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 400

    if len(content) > 1000:
        response = jsonify({'error': 'Message too long (max 1000 chars)'})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 400

    message = Message(
        content=content,
        user_id=session['user_id'],
        room_id=room_id
    )
    db.session.add(message)

    user = User.query.get(session['user_id'])
    user.last_seen = datetime.now()
    db.session.commit()

    response = jsonify({
        'success': True,
        'message': serialize_message(message)
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


# ============================================
# MEDIA UPLOAD (images, audio, video, voice, documents)
# ============================================
@app.route('/room/<int:room_id>/upload', methods=['POST'])
@login_required
def upload_media(room_id):
    room = Room.query.get_or_404(room_id)

    if 'file' not in request.files:
        response = jsonify({'error': 'No file provided'})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 400

    file = request.files['file']
    if not file or file.filename == '':
        response = jsonify({'error': 'No file selected'})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 400

    original_name = file.filename
    safe_name = secure_filename(original_name)

    if not safe_name:
        response = jsonify({'error': 'Invalid filename'})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 400

    media_type = get_media_type(safe_name)
    if not media_type:
        response = jsonify({'error': 'Unsupported file type: .' + safe_name.rsplit('.', 1)[-1]})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 400

    ext = safe_name.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)

    file.save(filepath)
    file_size = os.path.getsize(filepath)

    caption = request.form.get('caption', '').strip()

    message = Message(
        content=caption if caption else None,
        user_id=session['user_id'],
        room_id=room_id,
        media_type=media_type,
        media_filename=unique_name,
        media_original_name=original_name,
        media_size=file_size
    )
    db.session.add(message)

    user = User.query.get(session['user_id'])
    user.last_seen = datetime.now()
    db.session.commit()

    response = jsonify({
        'success': True,
        'message': serialize_message(message)
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ============================================
# GET MESSAGES (polling endpoint)
# ============================================
@app.route('/room/<int:room_id>/messages')
@login_required
def get_messages(room_id):
    room = Room.query.get_or_404(room_id)

    current_user = User.query.get(session['user_id'])
    current_user.last_seen = datetime.now()
    db.session.commit()

    since_id = request.args.get('since_id', type=int)

    query = Message.query.filter_by(room_id=room_id)
    if since_id:
        query = query.filter(Message.id > since_id)

    messages = query.order_by(Message.created_at.asc()).all()

    response = jsonify({
        'messages': [serialize_message(m) for m in messages]
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


# ============================================
# ONLINE USERS
# ============================================
@app.route('/room/<int:room_id>/online')
@login_required
def get_online_users(room_id):
    current_user = User.query.get(session['user_id'])
    current_user.last_seen = datetime.now()
    db.session.commit()

    cutoff = datetime.now() - timedelta(seconds=30)
    online_users = User.query.filter(User.last_seen >= cutoff).all()

    response = jsonify({
        'count': len(online_users),
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'is_me': u.id == session['user_id']
            }
            for u in online_users
        ]
    })
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


# ============================================
# DELETE ROOM
# ============================================
@app.route('/room/<int:room_id>/delete', methods=['POST'])
@login_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)

    if room.creator_id != session['user_id']:
        flash('You can only delete your own rooms.', 'error')
        return redirect(url_for('view_room', room_id=room.id))

    for msg in room.messages:
        if msg.media_filename:
            try:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], msg.media_filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f'Failed to delete file: {e}')

    db.session.delete(room)
    db.session.commit()

    flash(f'Room "{room.name}" deleted.', 'info')
    return redirect(url_for('index'))


# ============================================
# DELETE MESSAGE
# ============================================
@app.route('/message/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    room_id = message.room_id

    room = Room.query.get(room_id)
    if message.user_id != session['user_id'] and room.creator_id != session['user_id']:
        flash('You cannot delete this message.', 'error')
        return redirect(url_for('view_room', room_id=room_id))

    if message.media_filename:
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], message.media_filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f'Failed to delete file: {e}')

    db.session.delete(message)
    db.session.commit()

    flash('Message deleted.', 'info')
    return redirect(url_for('view_room', room_id=room_id))


# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)