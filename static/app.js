// CPS Wisdom Bot - Client JavaScript
var room = null, ub = null, bb = null, ld = null, muted = false, localIdentity = null;

function show() {
    document.getElementById('hero').classList.add('hide');
    document.getElementById('chat').classList.add('show');
}

// Auto-resize textarea and toggle buttons
function handleInput() {
    var inp = document.getElementById('inp');
    var sendBtn = document.getElementById('sendBtn');
    var voiceBtn = document.getElementById('voiceBtn');

    // Auto-resize
    inp.style.height = 'auto';
    inp.style.height = Math.min(inp.scrollHeight, 132) + 'px';

    // Toggle buttons based on content
    var hasText = inp.value.trim().length > 0;
    if (hasText) {
        sendBtn.classList.add('show');
        voiceBtn.classList.add('hide');
    } else {
        sendBtn.classList.remove('show');
        voiceBtn.classList.remove('hide');
    }
}

// Handle Enter key (send on Enter, new line on Shift+Enter)
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendText();
    }
}

// Scroll input into view on mobile keyboard open
function scrollInputIntoView() {
    setTimeout(function() {
        document.getElementById('inp').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
}

function addMsg(t, c, id) {
    var el = id ? document.getElementById(id) : null;
    if (el) {
        el.innerHTML = t;
        el.classList.remove('loading');
    } else {
        el = document.createElement('div');
        el.className = 'msg ' + c;
        if (id) el.id = id;
        el.innerHTML = t;
        document.getElementById('chat').appendChild(el);
    }
    var cDiv = document.getElementById('chat');
    cDiv.scrollTop = cDiv.scrollHeight;
    return el;
}

function loading(on) {
    if (on && !ld) {
        ld = addMsg('<div class="dots"><span></span><span></span><span></span></div>', 'bot loading', 'ld');
    }
    if (!on && ld) {
        ld.remove();
        ld = null;
    }
}

async function startVoice() {
    show();
    document.body.classList.add('calling');
    try {
        var t = await (await fetch('/voice/token')).json();
        room = new LivekitClient.Room();

        // Store local identity when connected
        room.on('connected', function() {
            localIdentity = room.localParticipant?.identity || null;
            console.log('✅ Connected. Local identity:', localIdentity);
        });

        room.on('trackSubscribed', function(track) {
            if (track.kind === 'audio') {
                var a = track.attach();
                a.volume = 1;
                document.body.appendChild(a);
                a.play();
            }
        });

        // Transcription handling
        room.on('transcriptionReceived', function(segs) {
            segs.forEach(function(s) {
                var participant = s.participant;
                var pid = null;

                if (typeof participant === 'string') {
                    pid = participant;
                } else if (participant && participant.identity) {
                    pid = participant.identity;
                } else if (participant && participant.sid) {
                    if (room.localParticipant && participant.sid === room.localParticipant.sid) {
                        pid = room.localParticipant.identity;
                    }
                }

                var isUser = false;
                if (pid) {
                    isUser = pid.startsWith('user_');
                    if (!isUser && localIdentity) {
                        isUser = (pid === localIdentity);
                    }
                    if (!isUser && (pid.includes('agent') || pid.includes('bot'))) {
                        isUser = false;
                    }
                } else {
                    isUser = true;
                }

                console.log('🔍 Transcription:', {
                    text: s.text,
                    participant: pid,
                    localIdentity: localIdentity,
                    isUser: isUser,
                    final: s.final
                });

                if (isUser) {
                    if (!ub) ub = 'u' + Date.now();
                    addMsg(s.text, 'user', ub);
                    if (s.final) { ub = null; loading(true); }
                } else {
                    loading(false);
                    if (!bb) bb = 'b' + Date.now();
                    addMsg(s.text, 'bot', bb);
                    if (s.final) bb = null;
                }
            });
        });

        await room.connect('wss://livekit.spiritualmessage.org', t.token);
        await room.localParticipant.setMicrophoneEnabled(true);
    } catch (e) {
        console.error('❌ Connection error:', e);
        endVoice();
    }
}

function toggleMute() {
    if (!room) return;
    muted = !muted;
    room.localParticipant.setMicrophoneEnabled(!muted);
    document.getElementById('muteBtn').style.background = muted ? '#fff' : '#444';
    document.getElementById('muteBtn').querySelector('svg').style.fill = muted ? '#000' : '#fff';
}

function endVoice() {
    if (room) room.disconnect();
    room = null;
    ub = null;
    bb = null;
    muted = false;
    localIdentity = null;
    document.body.classList.remove('calling');
    document.getElementById('muteBtn').style.background = '#444';
    loading(false);
}

async function sendText() {
    var i = document.getElementById('inp'), q = i.value.trim();
    if (!q) return;
    if (room) endVoice();
    show();
    i.value = '';

    // Reset textarea height and buttons
    i.style.height = 'auto';
    handleInput();

    addMsg(q, 'user');
    loading(true);
    try {
        var r = await fetch('/voice/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q })
        });
        var d = await r.json();
        loading(false);
        addMsg(d.answer || 'No response.', 'bot');
    } catch (e) {
        loading(false);
        addMsg('Error.', 'bot');
    }
}
