from __future__ import annotations
import os
import tempfile
import shutil
try:
    from flask import Flask, request, jsonify, abort
    from werkzeug.utils import send_file
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
from .auth import AuthManager, TokenProvider
from .registry import PackageRegistry

def create_app(registry_root: str = "./registry") -> Flask | None:
    """Create Flask app for EventFlow Hub API"""
    if not FLASK_AVAILABLE:
        return None
    app = Flask(__name__)

    auth_manager = AuthManager()
    registry = PackageRegistry(registry_root)

    def authenticate() -> str | None:
        """Get authenticated username from token"""
        token = request.headers.get('Authorization')
        if not token:
            return None
        if token.startswith('Bearer '):
            token = token[7:]
        return auth_manager.authenticate(token)

    @app.route('/')
    def index():
        return jsonify({"message": "EventFlow Hub API", "version": "0.1.0"})

    @app.route('/packages', methods=['GET'])
    def search_packages():
        query = request.args.get('q', '')
        domain = request.args.get('domain')
        author = request.args.get('author')
        packages = registry.search(query=query, domain=domain, author=author)
        return jsonify({"packages": packages})

    @app.route('/packages/<name>', methods=['GET'])
    def get_package(name: str):
        version = request.args.get('version')
        info = registry.get_package_info(name, version)
        if not info:
            abort(404, f"Package {name} not found")
        return jsonify(info)

    @app.route('/packages/<name>/<version>', methods=['GET'])
    def get_package_version(name: str, version: str):
        info = registry.get_package_info(name, version)
        if not info:
            abort(404, f"Package {name}:{version} not found")
        return jsonify(info)

    @app.route('/download/<name>/<version>', methods=['GET'])
    def download_package(name: str, version: str):
        pkg_path = registry.get_package_path(name, version)
        if not pkg_path:
            abort(404, f"Package {name}:{version} not found")

        # For now, return the directory as a zip
        import zipfile
        from io import BytesIO

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(pkg_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pkg_path)
                    zip_file.write(file_path, arcname)

        zip_buffer.seek(0)
        return send_file(zip_buffer, mimetype='application/zip',
                        as_attachment=True, download_name=f"{name}-{version}.efpkg.zip")

    @app.route('/publish', methods=['POST'])
    def publish_package():
        username = authenticate()
        if not username:
            abort(401, "Authentication required")

        if 'file' not in request.files:
            abort(400, "No file provided")

        file = request.files['file']
        if file.filename == '':
            abort(400, "No file selected")

        # Save uploaded file to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = os.path.join(temp_dir, file.filename)
            file.save(upload_path)

            # If it's a zip, extract it
            if file.filename.endswith('.zip'):
                import zipfile
                extract_dir = os.path.join(temp_dir, 'extracted')
                with zipfile.ZipFile(upload_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                package_dir = extract_dir
            else:
                # Assume it's a directory upload (for simplicity, treat as-is)
                package_dir = temp_dir

            try:
                package_key = registry.publish(package_dir, username)
                return jsonify({"message": f"Published {package_key}", "key": package_key}), 201
            except ValueError as e:
                abort(400, str(e))
            except Exception as e:
                abort(500, f"Publish failed: {e}")

    @app.route('/packages/<name>/<version>', methods=['DELETE'])
    def delete_package(name: str, version: str):
        username = authenticate()
        if not username:
            abort(401, "Authentication required")

        success = registry.delete_package(name, version, username)
        if not success:
            abort(403, "Cannot delete package")
        return jsonify({"message": f"Deleted {name}:{version}"})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)