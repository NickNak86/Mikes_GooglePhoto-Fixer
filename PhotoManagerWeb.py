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
import shutil
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Optional
from flask import Flask, render_template_string, jsonify, request, send_from_directory

# Try to import PhotoProcessor, but allow running without it for UI testing
try:
    from PhotoProcessor import PhotoProcessor, ProcessingIssue
    HAS_PROCESSOR = True
except ImportError:
    HAS_PROCESSOR = False
    print("Warning: PhotoProcessor not found. Running in UI-only mode.")

app = Flask(__name__)

# =============================================================================
# Configuration
# =============================================================================

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_SETTINGS = {
    "base_path": str(Path.home() / "PhotoLibrary"),
    "exiftool_path": "exiftool"
}

# Global state
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
    """Get local IP address for network access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def add_log(message):
    """Add message to processing log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    processing_status["log"].append(f"[{timestamp}] {message}")
    # Keep only last 100 messages
    if len(processing_status["log"]) > 100:
        processing_status["log"] = processing_status["log"][-100:]


# =============================================================================
# HTML Template - Mobile-First Material Design
# =============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#1a1a2e">
    <title>Google Photos Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
            padding-bottom: 100px;
        }

        .container {
            max-width: 500px;
            margin: 0 auto;
        }

        /* Header */
        .header {
            text-align: center;
            padding: 30px 0;
        }

        .header-icon {
            font-size: 64px;
            color: #e94560;
            margin-bottom: 10px;
        }

        .header h1 {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
            background: linear-gradient(90deg, #e94560, #0f3460);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            font-size: 14px;
            color: #a0a0a0;
        }

        /* Cards */
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .card-title .material-icons-round {
            color: #e94560;
        }

        /* Quick Start Steps */
        .steps {
            counter-reset: step;
        }

        .step {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            align-items: flex-start;
        }

        .step-number {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #e94560, #0f3460);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 16px;
            flex-shrink: 0;
        }

        .step-content h3 {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .step-content p {
            font-size: 13px;
            color: #a0a0a0;
            line-height: 1.5;
        }

        /* Buttons */
        .btn {
            width: 100%;
            padding: 18px 24px;
            border: none;
            border-radius: 15px;
            font-family: 'Poppins', sans-serif;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
            margin-bottom: 12px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #e94560, #0f3460);
            color: white;
            box-shadow: 0 10px 30px rgba(233, 69, 96, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(233, 69, 96, 0.4);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-primary:disabled {
            background: #3a3a5a;
            box-shadow: none;
            cursor: not-allowed;
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.15);
        }

        .btn-success {
            background: linear-gradient(135deg, #4CAF50, #2E7D32);
            color: white;
        }

        .btn-warning {
            background: linear-gradient(135deg, #FF9800, #F57C00);
            color: white;
        }

        /* Progress */
        .progress-container {
            margin: 20px 0;
        }

        .progress-bar {
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #e94560, #0f3460);
            border-radius: 4px;
            transition: width 0.3s ease;
            width: 0%;
        }

        .progress-text {
            font-size: 13px;
            color: #a0a0a0;
            text-align: center;
        }

        /* Status Badge */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: rgba(76, 175, 80, 0.2);
            border-radius: 20px;
            font-size: 13px;
            color: #4CAF50;
            margin-bottom: 15px;
        }

        .status-badge.processing {
            background: rgba(233, 69, 96, 0.2);
            color: #e94560;
        }

        .status-badge .dot {
            width: 8px;
            height: 8px;
            background: currentColor;
            border-radius: 50%;
        }

        .status-badge.processing .dot {
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }

        /* Log */
        .log-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.6;
            color: #a0a0a0;
        }

        .log-container::-webkit-scrollbar {
            width: 6px;
        }

        .log-container::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }

        /* Settings Form */
        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
            color: #a0a0a0;
        }

        .form-group input {
            width: 100%;
            padding: 15px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
        }

        .form-group input:focus {
            outline: none;
            border-color: #e94560;
        }

        /* Tabs */
        .tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 5px;
            margin-bottom: 20px;
        }

        .tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            border-radius: 12px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .tab.active {
            background: linear-gradient(135deg, #e94560, #0f3460);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Emoji Icons for Wife-Friendliness */
        .emoji-icon {
            font-size: 24px;
            margin-right: 5px;
        }

        /* Network Info */
        .network-info {
            text-align: center;
            padding: 15px;
            background: rgba(76, 175, 80, 0.1);
            border-radius: 12px;
            margin-top: 20px;
        }

        .network-info p {
            font-size: 12px;
            color: #a0a0a0;
            margin-bottom: 5px;
        }

        .network-info .url {
            font-size: 14px;
            font-weight: 600;
            color: #4CAF50;
            word-break: break-all;
        }

        /* Hide sections */
        .hidden {
            display: none !important;
        }

        /* Toast Notification */
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: #333;
            color: white;
            padding: 15px 25px;
            border-radius: 12px;
            font-size: 14px;
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
        }

        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        /* Help Tips */
        .tip {
            display: flex;
            gap: 12px;
            padding: 15px;
            background: rgba(233, 69, 96, 0.1);
            border-radius: 12px;
            margin-bottom: 15px;
            border-left: 3px solid #e94560;
        }

        .tip-icon {
            font-size: 20px;
        }

        .tip-text {
            font-size: 13px;
            line-height: 1.5;
            color: #e0e0e0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="header-icon">
                <span class="material-icons-round">photo_library</span>
            </div>
            <h1>Google Photos Manager</h1>
            <p>Organize your photos easily!</p>
        </div>

        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="showTab('home')">
                <span class="material-icons-round">home</span>
            </div>
            <div class="tab" onclick="showTab('guide')">
                <span class="material-icons-round">help</span>
            </div>
            <div class="tab" onclick="showTab('settings')">
                <span class="material-icons-round">settings</span>
            </div>
        </div>

        <!-- Home Tab -->
        <div id="tab-home" class="tab-content active">
            <!-- Status Card -->
            <div class="card">
                <div class="card-title">
                    <span class="material-icons-round">info</span>
                    Status
                </div>

                <div id="status-badge" class="status-badge">
                    <span class="dot"></span>
                    <span id="status-text">Ready to go!</span>
                </div>

                <div id="progress-section" class="progress-container hidden">
                    <div class="progress-bar">
                        <div id="progress-fill" class="progress-fill"></div>
                    </div>
                    <div id="progress-text" class="progress-text">Processing...</div>
                </div>
            </div>

            <!-- Action Card -->
            <div class="card">
                <div class="card-title">
                    <span class="material-icons-round">bolt</span>
                    What would you like to do?
                </div>

                <button id="btn-process" class="btn btn-primary" onclick="startProcessing()">
                    <span class="material-icons-round">auto_fix_high</span>
                    Organize My Photos
                </button>

                <button class="btn btn-warning" onclick="openReview()">
                    <span class="material-icons-round">rate_review</span>
                    Review Flagged Photos
                </button>

                <button class="btn btn-success" onclick="openLibrary()">
                    <span class="material-icons-round">folder_open</span>
                    Open My Photo Library
                </button>
            </div>

            <!-- Activity Log -->
            <div class="card">
                <div class="card-title">
                    <span class="material-icons-round">history</span>
                    Activity Log
                </div>
                <div id="log-container" class="log-container">
                    Welcome! Click "Organize My Photos" to start.
                </div>
            </div>
        </div>

        <!-- Guide Tab -->
        <div id="tab-guide" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <span class="emoji-icon">📱</span>
                    Quick Start Guide
                </div>

                <div class="tip">
                    <span class="tip-icon">💡</span>
                    <span class="tip-text">This guide will help you organize all your Google Photos in just a few easy steps!</span>
                </div>

                <div class="steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <div class="step-content">
                            <h3>Download Your Photos</h3>
                            <p>Go to <strong>takeout.google.com</strong> on your computer. Select "Google Photos" and download the ZIP file.</p>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">2</div>
                        <div class="step-content">
                            <h3>Put the ZIP File Here</h3>
                            <p>Move the downloaded ZIP file to:<br>
                            <strong id="takeout-path">PhotoLibrary/GoogleTakeout/</strong></p>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">3</div>
                        <div class="step-content">
                            <h3>Click "Organize My Photos"</h3>
                            <p>Press the big button and wait. The app will automatically sort everything by date!</p>
                        </div>
                    </div>

                    <div class="step">
                        <div class="step-number">4</div>
                        <div class="step-content">
                            <h3>Review (Optional)</h3>
                            <p>Click "Review Flagged Photos" to see any duplicates or blurry photos the app found.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-title">
                    <span class="emoji-icon">❓</span>
                    Common Questions
                </div>

                <div class="tip">
                    <span class="tip-icon">📁</span>
                    <span class="tip-text"><strong>Where do my photos go?</strong><br>They're organized into "Photos & Videos" folder, sorted by year and month.</span>
                </div>

                <div class="tip">
                    <span class="tip-icon">🗑️</span>
                    <span class="tip-text"><strong>Will it delete my photos?</strong><br>Never! Photos are only moved and organized, never deleted.</span>
                </div>

                <div class="tip">
                    <span class="tip-icon">📅</span>
                    <span class="tip-text"><strong>How does it fix dates?</strong><br>Google includes date info in JSON files. We restore those dates to your photos!</span>
                </div>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="tab-settings" class="tab-content">
            <div class="card">
                <div class="card-title">
                    <span class="material-icons-round">folder</span>
                    Photo Library Location
                </div>

                <div class="form-group">
                    <label>Where are your photos stored?</label>
                    <input type="text" id="base-path" placeholder="C:\\Users\\You\\PhotoLibrary">
                </div>

                <button class="btn btn-primary" onclick="saveSettings()">
                    <span class="material-icons-round">save</span>
                    Save Settings
                </button>
            </div>

            <div class="card">
                <div class="card-title">
                    <span class="material-icons-round">wifi</span>
                    Access from Your Phone
                </div>

                <div class="network-info">
                    <p>Open this URL on your phone:</p>
                    <div class="url" id="network-url">http://{{ local_ip }}:5000</div>
                </div>

                <div class="tip" style="margin-top: 15px;">
                    <span class="tip-icon">📱</span>
                    <span class="tip-text">Make sure your phone is on the same WiFi network as this computer!</span>
                </div>
            </div>
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        // Tab switching
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.closest('.tab').classList.add('active');
        }

        // Toast notifications
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        // Load settings on page load
        async function loadSettings() {
            try {
                const response = await fetch('/api/settings');
                const settings = await response.json();
                document.getElementById('base-path').value = settings.base_path || '';
                document.getElementById('takeout-path').textContent = settings.base_path + '/GoogleTakeout/';
            } catch (e) {
                console.error('Failed to load settings:', e);
            }
        }

        // Save settings
        async function saveSettings() {
            const basePath = document.getElementById('base-path').value;
            try {
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({base_path: basePath})
                });
                showToast('Settings saved! ✓');
                document.getElementById('takeout-path').textContent = basePath + '/GoogleTakeout/';
            } catch (e) {
                showToast('Failed to save settings');
            }
        }

        // Start processing
        async function startProcessing() {
            const btn = document.getElementById('btn-process');
            if (btn.disabled) return;

            if (!confirm('This will organize all photos in your GoogleTakeout folder.\\n\\nContinue?')) {
                return;
            }

            btn.disabled = true;
            document.getElementById('progress-section').classList.remove('hidden');
            document.getElementById('status-badge').classList.add('processing');

            try {
                await fetch('/api/process', {method: 'POST'});
                pollStatus();
            } catch (e) {
                showToast('Failed to start processing');
                btn.disabled = false;
            }
        }

        // Poll for status updates
        async function pollStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();

                document.getElementById('status-text').textContent = status.status;
                document.getElementById('progress-fill').style.width = status.progress + '%';
                document.getElementById('progress-text').textContent = status.status;
                document.getElementById('log-container').innerHTML = status.log.join('<br>');

                // Auto-scroll log
                const logContainer = document.getElementById('log-container');
                logContainer.scrollTop = logContainer.scrollHeight;

                if (status.is_processing) {
                    setTimeout(pollStatus, 1000);
                } else {
                    document.getElementById('btn-process').disabled = false;
                    document.getElementById('status-badge').classList.remove('processing');
                    if (status.progress >= 100) {
                        showToast('Done! Your photos are organized! 🎉');
                    }
                }
            } catch (e) {
                setTimeout(pollStatus, 2000);
            }
        }

        // Open review interface
        function openReview() {
            window.location.href = '/review';
        }

        // Open library folder
        async function openLibrary() {
            try {
                const response = await fetch('/api/open-library', {method: 'POST'});
                const result = await response.json();
                if (result.success) {
                    showToast('Opening folder...');
                } else {
                    showToast(result.message || 'Could not open folder');
                }
            } catch (e) {
                showToast('Failed to open folder');
            }
        }

        // Initialize
        loadSettings();

        // Check status on load
        fetch('/api/status').then(r => r.json()).then(status => {
            if (status.is_processing) {
                document.getElementById('btn-process').disabled = true;
                document.getElementById('progress-section').classList.remove('hidden');
                document.getElementById('status-badge').classList.add('processing');
                pollStatus();
            }
            if (status.log.length > 0) {
                document.getElementById('log-container').innerHTML = status.log.join('<br>');
            }
        });
    </script>
</body>
</html>
'''


# =============================================================================
# Routes
# =============================================================================

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
        # Demo mode - simulate processing
        threading.Thread(target=demo_processing).start()
        return jsonify({"success": True, "message": "Started (demo mode)"})

    # Start real processing in background
    threading.Thread(target=run_processing).start()
    return jsonify({"success": True})


def demo_processing():
    """Demo processing for testing UI without PhotoProcessor"""
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
    """Run actual photo processing"""
    global processing_status

    processing_status["is_processing"] = True
    processing_status["progress"] = 0
    processing_status["log"] = []
    add_log("Starting photo processing...")

    try:
        settings = load_settings()
        processor = PhotoProcessor(
            base_path=settings['base_path'],
            exiftool_path=settings.get('exiftool_path')
        )

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
        if os.name == 'nt':  # Windows
            os.startfile(str(library_path))
        else:  # macOS/Linux
            import subprocess
            subprocess.Popen(['xdg-open', str(library_path)])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/review')
def review():
    """Mobile-friendly review interface"""
    return render_template_string(REVIEW_TEMPLATE, local_ip=get_local_ip())


@app.route('/api/review/groups')
def get_review_groups():
    """Get all photo groups for review"""
    settings = load_settings()
    review_dir = Path(settings['base_path']) / "Pics Waiting for Approval"

    if not review_dir.exists():
        return jsonify({"groups": [], "message": "No photos to review"})

    groups = []
    # Match the folder names created by PhotoProcessor
    category_folders = [
        ('NEEDS ATTENTION - Duplicates', 'Duplicates'),
        ('NEEDS ATTENTION - Burst Photos', 'Burst Photos'),
        ('NEEDS ATTENTION - Blurry or Corrupt', 'Quality Issues'),
        ('NEEDS ATTENTION - Too Small', 'Too Small'),
        ('Duplicates', 'Duplicates'),
        ('Burst Photos', 'Burst Photos'),
        ('Quality Issues', 'Quality Issues'),
    ]

    for folder_name, category in category_folders:
        cat_dir = review_dir / folder_name
        if cat_dir.exists():
            for group_folder in cat_dir.iterdir():
                if group_folder.is_dir():
                    photos = []
                    for ext in ['.jpg', '.jpeg', '.png', '.heic', '.gif', '.webp']:
                        photos.extend([p.name for p in group_folder.glob(f'*{ext}')])
                        photos.extend([p.name for p in group_folder.glob(f'*{ext.upper()}')])

                    if photos:
                        best = next((p for p in photos if p.startswith('BEST_')), photos[0] if photos else None)
                        groups.append({
                            "id": str(group_folder),
                            "name": group_folder.name,
                            "category": category,
                            "photos": photos,
                            "best": best,
                            "count": len(photos)
                        })

    return jsonify({"groups": groups, "total": len(groups)})


@app.route('/api/review/photo/<path:photo_path>')
def get_review_photo(photo_path):
    """Serve a photo for review"""
    return send_from_directory('/', photo_path)


@app.route('/api/review/action', methods=['POST'])
def review_action():
    """Handle review actions (keep, delete, keep all)"""
    data = request.json
    action = data.get('action')
    group_path = data.get('group_path')
    photo = data.get('photo')

    settings = load_settings()
    library_path = Path(settings['base_path']) / "Photos & Videos"

    try:
        group_folder = Path(group_path)

        if action == 'keep_one':
            # Keep selected photo, move to library
            photo_path = group_folder / photo
            if photo_path.exists():
                # Organize by date
                from datetime import datetime
                mtime = datetime.fromtimestamp(photo_path.stat().st_mtime)
                dest_folder = library_path / str(mtime.year) / f"{mtime.month:02d}"
                dest_folder.mkdir(parents=True, exist_ok=True)

                # Remove BEST_ prefix if present
                new_name = photo.replace('BEST_', '')
                shutil.move(str(photo_path), str(dest_folder / new_name))

            # Delete the rest
            shutil.rmtree(str(group_folder), ignore_errors=True)
            return jsonify({"success": True, "message": f"Kept {photo}"})

        elif action == 'keep_all':
            # Move all photos to library
            for photo_file in group_folder.iterdir():
                if photo_file.is_file() and photo_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic', '.gif', '.webp']:
                    mtime = datetime.fromtimestamp(photo_file.stat().st_mtime)
                    dest_folder = library_path / str(mtime.year) / f"{mtime.month:02d}"
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    new_name = photo_file.name.replace('BEST_', '')
                    shutil.move(str(photo_file), str(dest_folder / new_name))

            shutil.rmtree(str(group_folder), ignore_errors=True)
            return jsonify({"success": True, "message": "Kept all photos"})

        elif action == 'delete_all':
            shutil.rmtree(str(group_folder), ignore_errors=True)
            return jsonify({"success": True, "message": "Deleted group"})

        return jsonify({"success": False, "message": "Unknown action"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


REVIEW_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#1a1a2e">
    <title>Review Photos</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }
        .header { background: rgba(0,0,0,0.3); padding: 15px 20px; display: flex; align-items: center; gap: 15px; position: sticky; top: 0; z-index: 100; }
        .header a { color: #e94560; text-decoration: none; font-size: 24px; }
        .header h1 { font-size: 18px; flex: 1; }
        .header .count { background: #e94560; padding: 5px 12px; border-radius: 20px; font-size: 12px; }
        .container { padding: 20px; max-width: 600px; margin: 0 auto; }
        .empty { text-align: center; padding: 60px 20px; }
        .empty .icon { font-size: 64px; color: #4CAF50; margin-bottom: 20px; }
        .empty h2 { color: #4CAF50; margin-bottom: 10px; }
        .empty p { color: #a0a0a0; }
        .group-card { background: rgba(255,255,255,0.05); border-radius: 16px; margin-bottom: 20px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }
        .group-header { padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .group-header h3 { font-size: 14px; font-weight: 600; }
        .group-header .badge { background: #e94560; padding: 4px 10px; border-radius: 12px; font-size: 11px; }
        .group-header .badge.duplicates { background: #FF9800; }
        .group-header .badge.burst { background: #2196F3; }
        .group-header .badge.quality { background: #f44336; }
        .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 8px; padding: 15px; }
        .photo-item { position: relative; aspect-ratio: 1; border-radius: 8px; overflow: hidden; cursor: pointer; border: 3px solid transparent; }
        .photo-item img { width: 100%; height: 100%; object-fit: cover; }
        .photo-item.selected { border-color: #4CAF50; }
        .photo-item.best::after { content: '★'; position: absolute; top: 5px; right: 5px; background: #4CAF50; color: white; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; }
        .group-actions { padding: 15px; display: flex; gap: 10px; border-top: 1px solid rgba(255,255,255,0.1); }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 10px; font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; }
        .btn-keep { background: #4CAF50; color: white; }
        .btn-keep-all { background: #2196F3; color: white; }
        .btn-delete { background: #f44336; color: white; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .loading { text-align: center; padding: 40px; }
        .loading .spinner { width: 40px; height: 40px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #e94560; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%) translateY(100px); background: #333; color: white; padding: 12px 24px; border-radius: 10px; opacity: 0; transition: all 0.3s; z-index: 1000; }
        .toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
        .fullscreen { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.95); z-index: 200; display: none; flex-direction: column; }
        .fullscreen.active { display: flex; }
        .fullscreen-header { padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .fullscreen-header button { background: none; border: none; color: white; font-size: 28px; cursor: pointer; }
        .fullscreen-image { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .fullscreen-image img { max-width: 100%; max-height: 100%; object-fit: contain; }
    </style>
</head>
<body>
    <div class="header">
        <a href="/"><span class="material-icons-round">arrow_back</span></a>
        <h1>Review Photos</h1>
        <div class="count" id="count">0 groups</div>
    </div>

    <div class="container" id="content">
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading photos...</p>
        </div>
    </div>

    <div class="fullscreen" id="fullscreen">
        <div class="fullscreen-header">
            <span id="fullscreen-name"></span>
            <button onclick="closeFullscreen()"><span class="material-icons-round">close</span></button>
        </div>
        <div class="fullscreen-image">
            <img id="fullscreen-img" src="" alt="">
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        let groups = [];
        let selectedPhotos = {};

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }

        async function loadGroups() {
            try {
                const res = await fetch('/api/review/groups');
                const data = await res.json();
                groups = data.groups;
                document.getElementById('count').textContent = groups.length + ' groups';
                renderGroups();
            } catch (e) {
                document.getElementById('content').innerHTML = '<div class="empty"><p>Error loading photos</p></div>';
            }
        }

        function renderGroups() {
            if (groups.length === 0) {
                document.getElementById('content').innerHTML = `
                    <div class="empty">
                        <div class="icon"><span class="material-icons-round">check_circle</span></div>
                        <h2>All Done!</h2>
                        <p>No photos need review. Great job!</p>
                        <p style="margin-top:20px"><a href="/" style="color:#e94560">← Back to Home</a></p>
                    </div>`;
                return;
            }

            let html = '';
            groups.forEach((g, idx) => {
                const badgeClass = g.category.toLowerCase().includes('duplicate') ? 'duplicates' :
                                   g.category.toLowerCase().includes('burst') ? 'burst' : 'quality';
                selectedPhotos[idx] = g.best;

                html += `
                <div class="group-card" id="group-${idx}">
                    <div class="group-header">
                        <h3>${g.name}</h3>
                        <span class="badge ${badgeClass}">${g.category} (${g.count})</span>
                    </div>
                    <div class="photo-grid">
                        ${g.photos.map(p => `
                            <div class="photo-item ${p === g.best ? 'best selected' : ''}"
                                 onclick="selectPhoto(${idx}, '${p}')"
                                 ondblclick="openFullscreen('${g.id}/${p}', '${p}')">
                                <img src="/api/review/photo/${g.id}/${p}" alt="${p}" loading="lazy">
                            </div>
                        `).join('')}
                    </div>
                    <div class="group-actions">
                        <button class="btn btn-keep" onclick="keepOne(${idx})">
                            <span class="material-icons-round">check</span> Keep Selected
                        </button>
                        <button class="btn btn-keep-all" onclick="keepAll(${idx})">
                            <span class="material-icons-round">done_all</span> Keep All
                        </button>
                        <button class="btn btn-delete" onclick="deleteAll(${idx})">
                            <span class="material-icons-round">delete</span>
                        </button>
                    </div>
                </div>`;
            });
            document.getElementById('content').innerHTML = html;
        }

        function selectPhoto(groupIdx, photo) {
            selectedPhotos[groupIdx] = photo;
            const card = document.getElementById('group-' + groupIdx);
            card.querySelectorAll('.photo-item').forEach(el => {
                el.classList.remove('selected');
                if (el.querySelector('img').src.includes(photo)) {
                    el.classList.add('selected');
                }
            });
        }

        function openFullscreen(path, name) {
            document.getElementById('fullscreen-img').src = '/api/review/photo/' + path;
            document.getElementById('fullscreen-name').textContent = name;
            document.getElementById('fullscreen').classList.add('active');
        }

        function closeFullscreen() {
            document.getElementById('fullscreen').classList.remove('active');
        }

        async function keepOne(idx) {
            const g = groups[idx];
            const photo = selectedPhotos[idx];
            try {
                const res = await fetch('/api/review/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action: 'keep_one', group_path: g.id, photo: photo })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Kept ' + photo);
                    groups.splice(idx, 1);
                    document.getElementById('count').textContent = groups.length + ' groups';
                    renderGroups();
                } else {
                    showToast('Error: ' + data.message);
                }
            } catch (e) { showToast('Error saving'); }
        }

        async function keepAll(idx) {
            const g = groups[idx];
            try {
                const res = await fetch('/api/review/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action: 'keep_all', group_path: g.id })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Kept all photos');
                    groups.splice(idx, 1);
                    document.getElementById('count').textContent = groups.length + ' groups';
                    renderGroups();
                } else {
                    showToast('Error: ' + data.message);
                }
            } catch (e) { showToast('Error saving'); }
        }

        async function deleteAll(idx) {
            if (!confirm('Delete all photos in this group?')) return;
            const g = groups[idx];
            try {
                const res = await fetch('/api/review/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action: 'delete_all', group_path: g.id })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Deleted');
                    groups.splice(idx, 1);
                    document.getElementById('count').textContent = groups.length + ' groups';
                    renderGroups();
                } else {
                    showToast('Error: ' + data.message);
                }
            } catch (e) { showToast('Error deleting'); }
        }

        document.addEventListener('keydown', e => { if (e.key === 'Escape') closeFullscreen(); });
        loadGroups();
    </script>
</body>
</html>
'''


# =============================================================================
# Main Entry Point
# =============================================================================

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

    # Open browser on Windows
    if os.name == 'nt':
        webbrowser.open(f'http://localhost:{port}')

    # Run Flask
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
