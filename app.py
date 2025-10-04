from flask import Flask, request

app = Flask(__name__)

@app.post('/repo')
def repo_create():
    json = request.get_json(force=True, silent=True)
    return 
