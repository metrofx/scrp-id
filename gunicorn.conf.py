# Konfigurasi Gunicorn
workers = 4
bind = "0.0.0.0:8000"
timeout = 120
# Ubah log path ke stdout/stderr untuk Docker best practice
accesslog = "-"
errorlog = "-" 