"""Application entry point for local development and production deployment."""

import os
from app.create_app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    # Render सर्वर पर पोर्ट नंबर डायनेमिक होता है, इसे environment variable से उठाना जरूरी है
    port = int(os.environ.get("PORT", 5000))
    
    # allow_unsafe_werkzeug=True लगाने से रेंडर पर प्रोडक्शन एरर नहीं आएगा
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        debug=app.config.get("DEBUG", False),
        allow_unsafe_werkzeug=True
    )
