/**
 * 🎮 WAREHOUSE ORCHESTRATOR UI - 8-BIT EDITION
 * JavaScript для интерактивности
 */

// ═══════════════════════════════════════════════════════════
// GLOBALS
// ═══════════════════════════════════════════════════════════

let terminalWs = null;
let agentWs = null;
let startTime = Date.now();

// Звуки (8-bit beeps) - можно включить если надо
const SOUNDS_ENABLED = false;

// ═══════════════════════════════════════════════════════════
// TERMINAL
// ═══════════════════════════════════════════════════════════

function log(message, type = 'info') {
    const terminal = document.getElementById('terminal-output');
    const time = new Date().toLocaleTimeString('ru-RU');

    // Убираем курсор
    const cursor = terminal.querySelector('.cursor');
    if (cursor) cursor.parentElement.remove();

    // Добавляем строку
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.innerHTML = `<span class="time">[${time}]</span> ${escapeHtml(message)}`;
    terminal.appendChild(line);

    // Добавляем курсор обратно
    const cursorLine = document.createElement('div');
    cursorLine.className = 'log-line';
    cursorLine.innerHTML = '<span class="cursor"></span>';
    terminal.appendChild(cursorLine);

    // Скроллим вниз
    terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
    const terminal = document.getElementById('terminal-output');
    terminal.innerHTML = `
        <div class="log-line info">
            <span class="time">[${new Date().toLocaleTimeString('ru-RU')}]</span>
            Terminal cleared. Ready for new adventures! 🎮
        </div>
        <div class="log-line">
            <span class="cursor"></span>
        </div>
    `;
    playSound('clear');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════════════════
// ACTIONS
// ═══════════════════════════════════════════════════════════

async function runAction(action, target) {
    playSound('select');

    // Disable кнопки
    setButtonsLoading(true);

    log(`Starting ${action} ${target}...`, 'warning');

    try {
        let response;

        if (action === 'deploy') {
            response = await fetch(`/api/deploy/${target}`, { method: 'POST' });
        } else if (action === 'tests') {
            response = await fetch(`/api/tests/${target}`, { method: 'POST' });
        }

        const data = await response.json();

        if (data.success) {
            log(data.message, 'success');
            playSound('success');
        } else {
            log(data.message, 'error');
            playSound('error');
        }

        // Выводим детали
        if (data.output) {
            data.output.split('\n').slice(0, 20).forEach(line => {
                if (line.trim()) log(line);
            });
        }

    } catch (error) {
        log(`Error: ${error.message}`, 'error');
        playSound('error');
    }

    setButtonsLoading(false);
    refreshStatus();
}

async function restartService(service) {
    playSound('select');

    log(`Restarting ${service}...`, 'warning');

    try {
        const response = await fetch(`/api/restart/${service}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            log(data.message, 'success');
            playSound('success');
        } else {
            log(data.message, 'error');
            playSound('error');
        }

    } catch (error) {
        log(`Error: ${error.message}`, 'error');
    }

    setTimeout(refreshStatus, 3000);
}

async function refreshStatus() {
    log('Refreshing status...', 'info');

    try {
        const response = await fetch('/api/status');
        const services = await response.json();

        // Обновляем карточки через HTMX
        htmx.trigger('#services-grid', 'htmx:load');

        // Обновляем системный индикатор
        const allLive = Object.values(services).every(s => s.status === 'live');
        const indicator = document.getElementById('system-indicator');

        if (allLive) {
            indicator.className = 'status-ok';
            indicator.textContent = '♥♥♥ SYSTEM OK ♥♥♥';
        } else {
            indicator.className = 'status-warn';
            indicator.textContent = '⚠ DEGRADED ⚠';
        }

        log('Status updated!', 'success');

    } catch (error) {
        log(`Failed to refresh: ${error.message}`, 'error');
    }
}

function setButtonsLoading(loading) {
    document.querySelectorAll('.btn-8bit').forEach(btn => {
        if (loading) {
            btn.classList.add('loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    });
}

// ═══════════════════════════════════════════════════════════
// AGENT CHAT
// ═══════════════════════════════════════════════════════════

async function sendAgentMessage() {
    const input = document.getElementById('agent-input-field');
    const message = input.value.trim();

    if (!message) return;

    playSound('select');

    // Очищаем поле
    input.value = '';

    // Добавляем сообщение пользователя
    addChatMessage('user', message);

    // Показываем "печатает"
    const typingId = showTyping();

    try {
        const response = await fetch('/api/agent/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        // Убираем "печатает"
        hideTyping(typingId);

        // Добавляем ответ
        addChatMessage('agent', data.response || data.error);
        playSound('message');

    } catch (error) {
        hideTyping(typingId);
        addChatMessage('agent', `🔥 Ошибка связи с агентом: ${error.message}`);
        playSound('error');
    }
}

function addChatMessage(role, text) {
    const chat = document.getElementById('agent-chat');

    const msg = document.createElement('div');
    msg.className = `chat-message ${role}`;
    msg.innerHTML = `
        <div class="author">${role === 'user' ? '👤 YOU' : '🤖 AGENT'}</div>
        <div class="text">${formatMessage(text)}</div>
    `;

    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
}

function formatMessage(text) {
    // Простое форматирование: переносы строк и code блоки
    return text
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code style="background: #1a1a1a; padding: 2px 6px;">$1</code>')
        .replace(/```([\s\S]*?)```/g, '<pre style="background: #1a1a1a; padding: 10px; overflow-x: auto;">$1</pre>');
}

function showTyping() {
    const chat = document.getElementById('agent-chat');
    const id = 'typing-' + Date.now();

    const typing = document.createElement('div');
    typing.id = id;
    typing.className = 'chat-message agent';
    typing.innerHTML = `
        <div class="author">🤖 AGENT</div>
        <div class="text" style="color: var(--gray);">Думаю<span class="dots">...</span></div>
    `;

    chat.appendChild(typing);
    chat.scrollTop = chat.scrollHeight;

    return id;
}

function hideTyping(id) {
    const typing = document.getElementById(id);
    if (typing) typing.remove();
}

// ═══════════════════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════════════════

function showModal(title, content, onConfirm) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-content').textContent = content;
    document.getElementById('modal').classList.add('active');

    document.getElementById('modal-confirm').onclick = () => {
        closeModal();
        if (onConfirm) onConfirm();
    };

    playSound('modal');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

// ═══════════════════════════════════════════════════════════
// UPTIME COUNTER
// ═══════════════════════════════════════════════════════════

function updateUptime() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const hours = String(Math.floor(elapsed / 3600)).padStart(2, '0');
    const minutes = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
    const seconds = String(elapsed % 60).padStart(2, '0');

    document.getElementById('uptime').textContent = `UPTIME: ${hours}:${minutes}:${seconds}`;
}

setInterval(updateUptime, 1000);

// ═══════════════════════════════════════════════════════════
// SOUNDS (8-bit beeps)
// ═══════════════════════════════════════════════════════════

const audioContext = new (window.AudioContext || window.webkitAudioContext)();

function playSound(type) {
    if (!SOUNDS_ENABLED) return;

    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    const sounds = {
        select: { freq: 800, duration: 0.1 },
        success: { freq: 1200, duration: 0.2 },
        error: { freq: 200, duration: 0.3 },
        message: { freq: 600, duration: 0.1 },
        modal: { freq: 400, duration: 0.15 },
        clear: { freq: 1000, duration: 0.05 }
    };

    const sound = sounds[type] || sounds.select;

    oscillator.frequency.value = sound.freq;
    oscillator.type = 'square'; // 8-bit звук!
    gainNode.gain.value = 0.1;

    oscillator.start();
    oscillator.stop(audioContext.currentTime + sound.duration);
}

// ═══════════════════════════════════════════════════════════
// KONAMI CODE EASTER EGG 🎮
// ═══════════════════════════════════════════════════════════

const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
let konamiIndex = 0;

document.addEventListener('keydown', (e) => {
    if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
            activateRainbowMode();
            konamiIndex = 0;
        }
    } else {
        konamiIndex = 0;
    }
});

function activateRainbowMode() {
    document.body.classList.add('rainbow-mode');
    log('🌈 RAINBOW MODE ACTIVATED! You found the easter egg! 🎮', 'success');

    setTimeout(() => {
        document.body.classList.remove('rainbow-mode');
    }, 10000);
}

// ═══════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════════════════

document.addEventListener('keydown', (e) => {
    // Не обрабатываем если в input
    if (e.target.tagName === 'INPUT') return;

    switch(e.key.toLowerCase()) {
        case 'd':
            if (e.ctrlKey) {
                e.preventDefault();
                runAction('deploy', 'all');
            }
            break;
        case 't':
            if (e.ctrlKey) {
                e.preventDefault();
                runAction('tests', 'e2e');
            }
            break;
        case 'r':
            if (e.ctrlKey) {
                e.preventDefault();
                refreshStatus();
            }
            break;
        case 'escape':
            closeModal();
            break;
    }
});

// ═══════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    log('Welcome to Warehouse Orchestrator! 🎮');
    log('Keyboard shortcuts: Ctrl+D (deploy), Ctrl+T (tests), Ctrl+R (refresh)');
    log('Try the Konami code for a surprise... ↑↑↓↓←→←→BA');

    // Фокус на поле ввода агента
    document.getElementById('agent-input-field').focus();
});
