import os
from flask import Flask, request, render_template, jsonify, redirect, url_for
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Configure Google OAuth
google_bp = make_google_blueprint(client_id='your_google_client_id',
                                    client_secret='your_google_client_secret',
                                    redirect_to='google_login')
app.register_blueprint(google_bp, url_prefix='/google_login')

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'google.login'  # Redirects to Google OAuth login if not authenticated

# In-memory storage for uploaded image names
uploaded_images = []

# Mock User class (you may want to replace this with a real User model)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Define a route for the home page
@app.route('/')
def home():
    return render_template('upload.html')

# Define a route to handle image upload and display the image name
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            # Save the uploaded image and store its name
            uploaded_images.append(file.filename)
            return redirect(url_for('render_image', image_name=file.filename))
    return "Image upload failed."

# Route for rendering the uploaded image
@app.route('/image/<image_name>')
@login_required
def render_image(image_name):
    return render_template('image.html', image_name=image_name)

# API route to list uploaded image names with rate limiting
@app.route('/api/images', methods=['GET'])
# @limiter.limit("5 per minute")  # Apply rate limiting here
def list_images():
    return jsonify(uploaded_images)

# Google OAuth login route
@app.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    response = google.get('/plus/v1/people/me')
    assert response.ok, response.text
    user_data = response.json()
    user_id = user_data['id']
    user = User(user_id)
    login_user(user)
    return redirect(url_for('home'))

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
