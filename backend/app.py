from flask import Flask
from functools import wraps
from blueprints.auth.auth import auth_bp
from blueprints.training_sessions.training_sessions import training_sessions_bp
from blueprints.positions.positions import positions_bp
from blueprints.techniques.techniques import techniques_bp
from blueprints.training_session_techniques.training_session_techniques import training_session_techniques_bp
from blueprints.technique_sequences.technique_sequences import technique_sequences_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(training_sessions_bp)
app.register_blueprint(positions_bp)
app.register_blueprint(techniques_bp)
app.register_blueprint(training_session_techniques_bp)
app.register_blueprint(technique_sequences_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5001)