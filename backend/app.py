from flask import Flask
from functools import wraps
from blueprints.auth.auth import auth_bp
from blueprints.training_sessions.training_sessions import training_sessions_bp
from blueprints.positions.positions import positions_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(training_sessions_bp)
app.register_blueprint(positions_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)