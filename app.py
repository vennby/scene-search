from flask import Flask, render_template, request, jsonify
from models import db, VideoClip
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Configure the database URI (using SQLite for example)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scene_search.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    clips = VideoClip.query.order_by(VideoClip.timestamp.desc()).all()
    return render_template('search.html', clips=clips)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        tags = request.form.get('tags')
        # Optionally handle file upload here
        clip = VideoClip(title=title, description=description, tags=tags)
        db.session.add(clip)
        db.session.commit()
        return jsonify({'message': 'Clip saved successfully!', 'redirect': '/search'})
    return render_template('upload.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()