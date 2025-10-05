def handle_server():
    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def home():
        return "Hello!"

    app.run(debug=False, port=5000)
