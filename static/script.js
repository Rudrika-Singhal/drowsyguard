// ================================================================
// DrowsyGuard — Main JavaScript
// ================================================================

const socket = io();
let stream = null;
let frameInterval = null;
let isDetecting = false;

// ================================================================
// SECTION NAVIGATION
// ================================================================

function showSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`section-${name}`).classList.add('active');
    event.target.classList.add('active');

    if (name === 'history') loadHistory();
    if (name !== 'live') stopCamera();
}

// ================================================================
// STATS LOAD
// ================================================================

async function loadStats() {
    try {
        const res  = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('statTotal').textContent  = data.total  || 0;
        document.getElementById('statDrowsy').textContent = data.drowsy || 0;
        document.getElementById('statAlert').textContent  = data.alert  || 0;
    } catch (e) {
        console.log('Stats load failed:', e);
    }
}

// ================================================================
// LIVE CAMERA
// ================================================================

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById('videoFeed');
        video.srcObject = stream;
        video.style.display = 'block';

        document.getElementById('cameraPlaceholder').style.display = 'none';
        document.getElementById('processedFeed').style.display     = 'none';
        document.getElementById('startBtn').style.display          = 'none';
        document.getElementById('stopBtn').style.display           = 'block';
        document.getElementById('calibrationOverlay').style.display = 'flex';

        // Status update
        setStatus('online', 'Calibrating...');

        isDetecting = true;

        // Send frames to server every 200ms
        frameInterval = setInterval(sendFrame, 1000);

    } catch (err) {
        alert('Camera access denied! Please allow camera permission.');
        console.error(err);
    }
}

function stopCamera() {
    isDetecting = false;

    if (frameInterval) {
        clearInterval(frameInterval);
        frameInterval = null;
    }

    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }

    const video = document.getElementById('videoFeed');
    video.srcObject = null;
    video.style.display = 'none';

    document.getElementById('processedFeed').style.display      = 'none';
    document.getElementById('cameraPlaceholder').style.display  = 'flex';
    document.getElementById('startBtn').style.display           = 'block';
    document.getElementById('stopBtn').style.display            = 'none';
    document.getElementById('calibrationOverlay').style.display = 'none';
    document.getElementById('alertBox').style.display           = 'none';

    setStatus('offline', 'Offline');
    resetSignals();
}

function sendFrame() {
    if (!isDetecting || !stream) return;

    const video  = document.getElementById('videoFeed');
    const canvas = document.getElementById('overlayCanvas');
    canvas.width  = 640;
    canvas.height = 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, 640, 480);

    const frameData = canvas.toDataURL('image/jpeg', 0.7);
    socket.emit('frame', { frame: frameData });
}

// ================================================================
// SOCKET EVENTS
// ================================================================

socket.on('connect', () => {
    console.log('Socket connected');
});

socket.on('calibrating', (data) => {
    document.getElementById('calProgress').style.width = data.progress + '%';
    document.getElementById('calPercent').textContent  = data.progress + '%';
});

socket.on('calibration_done', (data) => {
    // Calibration overlay hatao — video feed waise hi chalta rahe
    document.getElementById('calibrationOverlay').style.display = 'none';
    document.getElementById('videoFeed').style.display          = 'block';
    setStatus('detecting', 'Detecting...');
    console.log('Calibration done, EAR baseline:', data.ear);
});

socket.on('result', (data) => {
    updateLiveResult(data);
});

// ================================================================
// UPDATE LIVE RESULT UI
// ================================================================

function updateLiveResult(data) {
    // Live camera feed directly dikhao — server se image mat lao
    // Video feed already chal raha hai browser mein

    // EAR & Score
    document.getElementById('liveEAR').textContent   = data.ear || '--';
    document.getElementById('liveScore').textContent = data.fatigue_score || 0;

    // Status
    const label = document.getElementById('statusLabel');
    const icon  = document.getElementById('statusIcon');

    if (data.result === 'DROWSY') {
        label.textContent = 'DROWSY!';
        label.className   = 'status-label drowsy';
        icon.textContent  = '🔴';
        document.getElementById('alertBox').style.display = 'block';
        setStatus('drowsy', 'DROWSY DETECTED');
        triggerDrowsyAlert(); // 🔔 Beep + Voice alert
    } else if (data.result === 'ALERT') {
        label.textContent = 'ALERT';
        label.className   = 'status-label alert';
        icon.textContent  = '🟢';
        document.getElementById('alertBox').style.display = 'none';
        setStatus('detecting', 'Detecting...');
    } else {
        label.textContent = data.result || 'Waiting...';
        label.className   = 'status-label';
        icon.textContent  = '🟡';
    }

    // Signals
    const signals = data.signals || {};
    updateSignal('sig-eye',  signals.eye_closed);
    updateSignal('sig-yawn', signals.yawning);
    updateSignal('sig-nod',  signals.head_nodding);
    updateSignal('sig-tilt', signals.head_tilted);
    updateSignal('sig-away', signals.looking_away);
}

function updateSignal(id, isOn) {
    const dot = document.querySelector(`#${id} .sig-dot`);
    if (!dot) return;
    dot.className = 'sig-dot ' + (isOn ? 'on' : 'off');
}

function resetSignals() {
    ['sig-eye','sig-yawn','sig-nod','sig-tilt','sig-away'].forEach(id => {
        updateSignal(id, false);
    });
    document.getElementById('liveEAR').textContent   = '--';
    document.getElementById('liveScore').textContent = '--';
    document.getElementById('statusLabel').textContent = 'Waiting...';
    document.getElementById('statusLabel').className   = 'status-label';
    document.getElementById('statusIcon').textContent  = '🟡';
}

function setStatus(type, text) {
    const dot  = document.getElementById('statusDot');
    const span = document.getElementById('statusText');
    dot.className  = 'status-dot ' + type;
    span.textContent = text;
}

// ================================================================
// IMAGE UPLOAD
// ================================================================

function handleImageDrop(e) {
    e.preventDefault();
    document.getElementById('imageDropZone').classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) uploadImage(file);
}

function handleImageSelect(e) {
    const file = e.target.files[0];
    if (file) uploadImage(file);
}

async function uploadImage(file) {
    document.getElementById('imageResult').style.display  = 'none';
    document.getElementById('imageLoading').style.display = 'flex';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res  = await fetch('/api/analyze/image', {
            method: 'POST',
            body  : formData
        });
        const data = await res.json();

        document.getElementById('imageLoading').style.display = 'none';

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        showImageResult(data);
        loadStats();

    } catch (err) {
        document.getElementById('imageLoading').style.display = 'none';
        alert('Upload failed: ' + err.message);
    }
}

function showImageResult(data) {
    const resultDiv = document.getElementById('imageResult');
    const preview   = document.getElementById('imagePreview');
    const badge     = document.getElementById('imageBadge');
    const details   = document.getElementById('imageDetails');

    if (data.annotated) {
        preview.src = 'data:image/jpeg;base64,' + data.annotated;
    }

    badge.textContent = data.result === 'DROWSY' ? '⚠️ DROWSY' : '✅ ALERT';
    badge.className   = 'result-badge ' + data.result.toLowerCase();

    const signals = data.signals || {};
    details.innerHTML = `
        <span>Fatigue Score: ${data.fatigue_score}</span>
        <span>EAR: ${data.ear}</span>
        <span>Eyes Closed: ${signals.eye_closed ? '✓' : '✗'}</span>
        <span>Yawning: ${signals.yawning ? '✓' : '✗'}</span>
        <span>Head Nodding: ${signals.head_nodding ? '✓' : '✗'}</span>
    `;

    resultDiv.style.display = 'block';
}

// ================================================================
// VIDEO UPLOAD
// ================================================================

function handleVideoDrop(e) {
    e.preventDefault();
    document.getElementById('videoDropZone').classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) uploadVideo(file);
}

function handleVideoSelect(e) {
    const file = e.target.files[0];
    if (file) uploadVideo(file);
}

async function uploadVideo(file) {
    document.getElementById('videoResult').style.display  = 'none';
    document.getElementById('videoLoading').style.display = 'flex';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res  = await fetch('/api/analyze/video', {
            method: 'POST',
            body  : formData
        });
        const data = await res.json();

        document.getElementById('videoLoading').style.display = 'none';

        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }

        showVideoResult(data);
        loadStats();

    } catch (err) {
        document.getElementById('videoLoading').style.display = 'none';
        alert('Upload failed: ' + err.message);
    }
}

function showVideoResult(data) {
    const resultDiv = document.getElementById('videoResult');
    const preview   = document.getElementById('videoPreview');
    const badge     = document.getElementById('videoBadge');
    const details   = document.getElementById('videoDetails');

    if (data.annotated) {
        preview.src = 'data:image/jpeg;base64,' + data.annotated;
    }

    badge.textContent = data.result === 'DROWSY' ? '⚠️ DROWSY' : '✅ ALERT';
    badge.className   = 'result-badge ' + data.result.toLowerCase();

    details.innerHTML = `
        <span>Overall Result: ${data.result}</span>
        <span>Avg Fatigue Score: ${data.fatigue_score}</span>
        <span>Drowsy Frames: ${data.drowsy_percent}% of video</span>
        <span>Frames Analyzed: ${data.total_frames}</span>
    `;

    resultDiv.style.display = 'block';
}

// ================================================================
// HISTORY
// ================================================================

async function loadHistory() {
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Loading...</td></tr>';

    try {
        const res      = await fetch('/api/history');
        const sessions = await res.json();

        if (!sessions.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-row">No sessions yet</td></tr>';
            return;
        }

        tbody.innerHTML = sessions.map((s, i) => {
            const signals  = s.signals || {};
            const sigList  = Object.entries(signals)
                .filter(([k,v]) => v)
                .map(([k]) => k.replace('_', ' '))
                .join(', ') || 'none';

            const badgeClass = s.result === 'DROWSY' ? 'badge-drowsy' : 'badge-alert';

            return `
                <tr>
                    <td>${i+1}</td>
                    <td>${s.timestamp}</td>
                    <td><span class="badge badge-type">${s.test_type}</span></td>
                    <td><span class="badge ${badgeClass}">${s.result}</span></td>
                    <td>${s.fatigue_score}</td>
                    <td style="color: var(--text2); font-size:0.75rem">${sigList}</td>
                </tr>
            `;
        }).join('');

    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Failed to load history</td></tr>';
    }
}

// ================================================================
// ALERT SOUND & VOICE
// ================================================================

let lastAlertTime   = 0;
let alertPlaying    = false;
const ALERT_COOLDOWN = 8000; // 8 seconds

function playBeep() {
    try {
        const ctx  = new (window.AudioContext || window.webkitAudioContext)();
        const osc  = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.frequency.value = 1000;
        osc.type            = 'square';
        gain.gain.value     = 0.3;

        osc.start();
        setTimeout(() => {
            osc.stop();
            ctx.close();
        }, 800);
    } catch(e) {
        console.log('Audio error:', e);
    }
}

function speakAlert(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // purani speech band karo
    const utter  = new SpeechSynthesisUtterance(text);
    utter.rate   = 0.9;
    utter.volume = 1;
    utter.pitch  = 1;
    window.speechSynthesis.speak(utter);
}

function triggerDrowsyAlert() {
    const now = Date.now();
    if (now - lastAlertTime < ALERT_COOLDOWN) return; // cooldown
    lastAlertTime = now;

    // Beep sound
    playBeep();

    // Voice alert
    setTimeout(() => {
        speakAlert("Warning! Driver drowsiness detected. Please take a break.");
    }, 200);

    // Red flash on screen
    document.body.style.border = '4px solid red';
    setTimeout(() => {
        document.body.style.border = 'none';
    }, 1000);
}

// ================================================================
// INIT
// ================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
});