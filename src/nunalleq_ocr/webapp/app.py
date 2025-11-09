"""
Flask web application for Nunalleq OCR.

A simple, user-friendly web interface for archaeologists.
"""

import os
import json
import tempfile
import shutil
import zipfile
import webbrowser
from pathlib import Path
from threading import Thread
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

from ..detector import ArtifactDetector
from ..renamer import ArtifactRenamer


# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='nunalleq_uploads_')
app.config['OUTPUT_FOLDER'] = tempfile.mkdtemp(prefix='nunalleq_output_')

# Global state (in production, use proper session management)
current_task = {
    'status': 'idle',
    'progress': 0,
    'message': '',
    'results': None
}


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/upload_and_process', methods=['POST'])
def upload_and_process():
    """Handle file upload and processing."""
    global current_task

    # Check if files were uploaded
    if 'photos' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('photos')

    if len(files) == 0:
        return jsonify({'error': 'No files selected'}), 400

    # Reset task state
    current_task = {
        'status': 'running',
        'progress': 0,
        'message': 'Uploading photos...',
        'results': None
    }

    # Clean up old uploads
    upload_folder = Path(app.config['UPLOAD_FOLDER'])
    output_folder = Path(app.config['OUTPUT_FOLDER'])

    # Clear folders
    for folder in [upload_folder, output_folder]:
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    # Save uploaded files
    saved_files = []
    for file in files:
        if file and file.filename:
            filename = secure_filename(file.filename)
            if filename.lower().endswith(('.jpg', '.jpeg')):
                filepath = upload_folder / filename
                file.save(filepath)
                saved_files.append(filepath)

    if len(saved_files) == 0:
        return jsonify({'error': 'No valid JPG files found'}), 400

    # Run processing in background
    thread = Thread(
        target=_process_uploaded_files,
        args=(saved_files, output_folder),
        daemon=True
    )
    thread.start()

    return jsonify({'status': 'started'})


def _process_uploaded_files(input_files, output_folder):
    """Worker function to process uploaded images."""
    global current_task

    try:
        current_task['message'] = f'Processing {len(input_files)} photos...'
        current_task['progress'] = 10

        detector = ArtifactDetector()
        renamer = ArtifactRenamer(detector=detector)

        # Process each file
        results = {
            'total': len(input_files),
            'success': 0,
            'failed': 0,
            'results': []
        }

        for i, input_file in enumerate(input_files):
            try:
                # Update progress
                progress = 10 + int((i / len(input_files)) * 80)
                current_task['progress'] = progress
                current_task['message'] = f'Processing {i+1}/{len(input_files)}: {input_file.name}'

                # Rename the file
                success, message = renamer.rename_file(
                    input_file,
                    output_dir=output_folder,
                    overwrite=False
                )

                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['results'].append({
                    'success': success,
                    'message': message
                })

            except Exception as e:
                results['failed'] += 1
                results['results'].append({
                    'success': False,
                    'message': f'{input_file.name}: Error - {str(e)}'
                })

        # Create ZIP file if there were successful renames
        zip_path = None
        if results['success'] > 0:
            current_task['message'] = 'Creating download package...'
            current_task['progress'] = 90

            zip_path = Path(app.config['OUTPUT_FOLDER']) / 'renamed_photos.zip'

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in output_folder.glob('*.jpg'):
                    zipf.write(file, file.name)

        current_task['status'] = 'complete'
        current_task['progress'] = 100
        current_task['message'] = f"Completed! Processed {results['success']} of {results['total']} photos"
        current_task['results'] = {
            'total': results['total'],
            'success': results['success'],
            'failed': results['failed'],
            'zip_available': zip_path is not None,
            'details': results['results']
        }

    except Exception as e:
        current_task['status'] = 'error'
        current_task['message'] = str(e)
        current_task['results'] = None


@app.route('/api/status')
def get_status():
    """Get current task status."""
    return jsonify(current_task)


@app.route('/api/reset')
def reset():
    """Reset task state."""
    global current_task
    current_task = {
        'status': 'idle',
        'progress': 0,
        'message': '',
        'results': None
    }
    return jsonify({'status': 'reset'})


@app.route('/api/download_results')
def download_results():
    """Download the ZIP file of renamed photos."""
    zip_path = Path(app.config['OUTPUT_FOLDER']) / 'renamed_photos.zip'

    if not zip_path.exists():
        return jsonify({'error': 'No results available for download'}), 404

    return send_file(
        zip_path,
        as_attachment=True,
        download_name='nunalleq_renamed_photos.zip',
        mimetype='application/zip'
    )


def open_browser():
    """Open web browser to the app."""
    webbrowser.open('http://127.0.0.1:5000')


def main(port=5000, debug=False):
    """Run the Flask app."""
    print("="*60)
    print("  Nunalleq Artifact Photo Organizer")
    print("="*60)
    print(f"\nStarting web interface on http://127.0.0.1:{port}")
    print("\n Your web browser should open automatically.")
    print(" If it doesn't, open your browser and go to:")
    print(f"   http://127.0.0.1:{port}")
    print("\nPress Ctrl+C to stop the server.\n")

    # Open browser after a short delay
    if not debug:
        Thread(target=lambda: (
            __import__('time').sleep(1.5),
            open_browser()
        ), daemon=True).start()

    try:
        app.run(host='127.0.0.1', port=port, debug=debug)
    finally:
        # Clean up temp folders on exit
        for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
            if os.path.exists(folder):
                try:
                    shutil.rmtree(folder)
                except:
                    pass


if __name__ == '__main__':
    main()
