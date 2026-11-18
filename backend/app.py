from flask import Flask
from functools import wraps
from blueprints.auth.auth import auth_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)