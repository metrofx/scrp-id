from flask import Flask

app = Flask(__name__)

# Import routes setelah app dibuat untuk menghindari circular import
from scrapp import routes, app 