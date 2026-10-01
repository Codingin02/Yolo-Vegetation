from __future__ import annotations

import os
import secrets

from flask import Flask, jsonify, redirect, request

from .routes import limiter, vegetation


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=4 * 1024 * 1024,
        SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
    )
    if test_config:
        app.config.update(test_config)
    limiter.init_app(app)
    app.register_blueprint(vegetation)

    @app.after_request
    def secure_response(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "media-src 'self' blob:; object-src 'none'; base-uri 'self'; "
            "form-action 'self'; frame-ancestors 'none'"
        )
        response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
        return response

    @app.errorhandler(413)
    def request_too_large(_):
        if request.path.startswith("/api/"):
            return jsonify({"status": "request_too_large", "error": "request too large"}), 413
        return "Berkas terlalu besar", 413

    @app.errorhandler(429)
    def rate_limited(_):
        if request.path.startswith("/api/"):
            return jsonify({"status": "rate_limited", "error": "too many requests"}), 429
        return "Terlalu banyak permintaan", 429

    @app.errorhandler(500)
    def internal_error(exc):
        original = getattr(exc, "original_exception", exc)
        app.logger.error("Unhandled request error: %s", type(original).__name__)
        if request.path.startswith("/api/"):
            return jsonify({"status": "error", "error": "request could not be processed"}), 500
        return "Permintaan tidak dapat diproses", 500

    @app.get("/")
    def index():
        return redirect("/vegetation")

    return app
