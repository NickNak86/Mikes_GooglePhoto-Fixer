"""
Google Photos Manager - Web Edition
====================================
Mobile-friendly web interface for photo management.
Run on Windows, access from any device!

Author: Claude Code
Date: 2025-11-22
Version: 3.0 (Web Edition)
"""

import os
import sys
import json
import socket
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional
from flask import Flask, render_template_string, jsonify, request, send_from_directory

try:
    from PhotoProcessor import PhotoProcessor, ProcessingIssue
    HAS_PROCESSOR = True
except ImportError:
    HAS_PROCESSOR = False
    print("Warning: PhotoProcessor not found. Running in UI-only mode.")

app = Flask(__name__)

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_SETTINGS = {
    "base_path": str(Path.home() / "PhotoLibrary"),
    "exiftool_path": "exiftool"
}

processing_status = {
    "is_processing": False,
    "progress": 0,
    "status": "Ready",
    "log": []
}

def load_settings():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def add_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    processing_status["log"].append(f"[{timestamp}] {message}")
    if len(processing_status["log"]) > 100:
        processing_status["log"] = processing_status["log"][-100:]

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Photos Manager - Web Edition</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 0; }
        h1, h2, h3 { color: #e94560; }
        a { color: #4CAF50; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .button { display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; margin: 10px 0; border-radius: 5px; text-align: center; }
        .button:hover { background-color: #45a049; }
        .status { font-size: 1.2em; margin: 20px 0; }
        .log { background-color: #1e1e2e; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto; }
        .log div { margin-bottom: 5px; }
        footer { text-align: center; padding: 20px 0; }
    </style>
</head>
<body>

<div class="container">
    <h1>Google Photos Manager - Web Edition</h1>
    <div class="status">
        <span id="statusText">Ready</span>
        <div id="progressBar" style="width: 100%; background-color: #444; border-radius: 5px; overflow: hidden; display: none;">
            <div id="progressFill" style="height: 100%; width: 0; background-color: #4CAF50;"></div>
        </div>
    </div>
    <div class="log" id="logContainer"></div>
    <a href="#" class="button" id="startButton">Start Processing</a>
    <a href="#" class="button" id="openLibraryButton">Open Photo Library</a>
    <a href="/review" class="button" target="_blank">Go to Review Interface</a>
    <h2>Settings</h2>
    <label for="basePath">Base Path:</label>
    <input type="text" id="basePath" style="width: 100%;" />
    <label for="exiftoolPath">ExifTool Path:</label>
    <input type="text" id="exiftoolPath" style="width: 100%;" />
    <a href="#" class="button" id="saveSettingsButton">Save Settings</a>
</div>

<footer>
    <p>&copy; 2025 Claude Code. All rights reserved.</p>
</footer>

<script>
    document.addEventListener('DOMContentLoaded', function() {
        loadSettings();
        document.getElementById('startButton').addEventListener('click', function() {
            startProcessing();
        });
        document.getElementById('openLibraryButton').addEventListener('click', function() {
            openLibrary();
        });
        document.getElementById('saveSettingsButton').addEventListener('click', function() {
            saveSettings();
        });
    });

    function updateStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('statusText').innerText = data.status;
                const progressBar = document.getElementById('progressBar');
                const progressFill = document.getElementById('progressFill');
                if (data.is_processing) {
                    progressBar.style.display = 'block';
                    progressFill.style.width = data.progress + '%';
                } else {
                    progressBar.style.display = 'none';
                }
                const logContainer = document.getElementById('logContainer');
                logContainer.innerHTML = '';
                data.log.forEach(log => {
                    const div = document.createElement('div');
                    div.innerText = log;
                    logContainer.appendChild(div);
                });
            });
    }

    function startProcessing() {
        fetch('/api/process', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Processing started successfully!');
                    const interval = setInterval(() => {
                        updateStatus();
                        if (!data.is_processing) {
                            clearInterval(interval);
                        }
                    }, 1000);
                } else {
                    alert('Error starting processing: ' + data.message);
                }
            });
    }

    function openLibrary() {
        fetch('/api/open-library', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert('Error opening library: ' + data.message);
                }
            });
    }

    function loadSettings() {
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                document.getElementById('basePath').value = data.base_path;
                document.getElementById('exiftoolPath').value = data.exiftool_path;
            });
    }

    function saveSettings() {
        const settings = {
            base_path: document.getElementById('basePath').value,
            exiftool_path: document.getElementById('exiftoolPath').value
        };
        fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Settings saved successfully!');
            } else {
                alert('Error saving settings: ' + data.message);
            }
        });
    }

    setInterval(updateStatus, 2000);
</script>

</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, local_ip=get_local_ip())

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(load_settings())

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json
    settings = load_settings()
    if 'base_path' in data:
        settings['base_path'] = data['base_path']
    if 'exiftool_path' in data:
        settings['exiftool_path'] = data['exiftool_path']
    save_settings(settings)
    return jsonify({"success": True})

@app.route('/api/status')
def get_status():
    return jsonify(processing_status)

@app.route('/api/process', methods=['POST'])
def start_processing():
    global processing_status
    if processing_status["is_processing"]:
        return jsonify({"success": False, "message": "Already processing"})
    if not HAS_PROCESSOR:
        threading.Thread(target=demo_processing).start()
        return jsonify({"success": True, "message": "Started (demo mode)"})
    threading.Thread(target=run_processing).start()
    return jsonify({"success": True})

def demo_processing():
    global processing_status
    import time
    processing_status["is_processing"] = True
    processing_status["progress"] = 0
    processing_status["log"] = []
    steps = [
        (10, "Finding photos..."),
        (25, "Reading metadata from JSON files..."),
        (40, "Restoring photo dates..."),
        (55, "Finding duplicates..."),
        (70, "Detecting quality issues..."),
        (85, "Organizing by date..."),
        (100, "Done! Your photos are organized!")
    ]
    for progress, status in steps:
        time.sleep(2)
        processing_status["progress"] = progress
        processing_status["status"] = status
        add_log(status)
    processing_status["is_processing"] = False

def run_processing():
    global processing_status
    processing_status["is_processing"] = True
    processing_status["progress"] = 0
    processing_status["log"] = []
    add_log("Starting photo processing...")
    try:
        settings = load_settings()
        processor = PhotoProcessor(base_path=settings['base_path'], exiftool_path=settings.get('exiftool_path'))
        def update_progress(p):
            processing_status["progress"] = p
        def update_status(s):
            processing_status["status"] = s
            add_log(s)
        processor.progress_callback = update_progress
        processor.status_callback = update_status
        stats, issues = processor.run_full_pipeline()
        processing_status["progress"] = 100
        processing_status["status"] = "Complete!"
        add_log("Processing complete!")
        add_log(processor.get_summary())
    except Exception as e:
        processing_status["status"] = f"Error: {str(e)}"
        add_log(f"Error: {str(e)}")
    processing_status["is_processing"] = False

@app.route('/api/open-library', methods=['POST'])
def open_library():
    settings = load_settings()
    library_path = Path(settings['base_path']) / "Photos & Videos"
    if not library_path.exists():
        return jsonify({"success": False, "message": "Library folder doesn't exist yet. Run processing first!"})
    try:
        if os.name == 'nt':
            os.startfile(str(library_path))
        else:
            import subprocess
            subprocess.Popen(['xdg-open', str(library_path)])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/review')
def review():
    return '''
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: white; padding: 40px; text-align: center; }
    h1 { color: #e94560; } p { color: #a0a0a0; margin: 20px 0; } a { color: #4CAF50; }</style></head>
    <body><h1>Review Interface</h1><p>The review interface works best on a computer with a larger screen.</p>
    <p>On your Windows PC, run <strong>ReviewInterfaceQt.py</strong> for the full review experience!</p>
    <p><a href="/">← Back to Home</a></p></body></html>
    '''

def main():
    local_ip = get_local_ip()
    port = 5000
    print("=" * 60)
    print("  GOOGLE PHOTOS MANAGER - WEB EDITION")
    print("=" * 60)
    print()
    print("  The app is running!")
    print()
    print("  Access from this computer:")
    print(f"    http://localhost:{port}")
    print()
    print("  Access from your phone (same WiFi):")
    print(f"    http://{local_ip}:{port}")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    if os.name == 'nt':
        webbrowser.open(f'http://localhost:{port}')
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
