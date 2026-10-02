from .api import bp as api_bp
from .health import bp as health_bp
from .web import bp as web_bp

all_blueprints = (web_bp, api_bp, health_bp)
