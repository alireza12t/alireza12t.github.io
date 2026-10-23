// Owner admin. The page holds nothing secret: every booking read or change goes
// to the booking Lambda, which checks the password + authenticator code and
// hands back a signed 8-hour token. The token lives in sessionStorage, so it
// is gone when the tab closes.
(function () {
    const API = 'https://r7n6gzfefcwld37lyjkabauqk40sqydj.lambda-url.us-east-1.on.aws/admin';
    const TOKEN_KEY = 'bookingAdminToken';
    const $ = (id) => document.getElementById(id);

    // Match the site's light/dark choice
    try {
        const theme = localStorage.getItem('theme');
        if (theme) document.documentElement.setAttribute('data-theme', theme);
    } catch { /* storage blocked */ }

    // ── Tabs ────────────────────────────────────────────────────────────────
    const tabs = ['booking', 'figbo'];
    function showTab(name) {
        if (!tabs.includes(name)) name = 'booking';
        tabs.forEach((t) => {
            $('tab-' + t).setAttribute('aria-selected', String(t === name));
            $(t).hidden = t !== name;
        });
        history.replaceState(null, '', name === 'booking' ? location.pathname : '#' + name);
    }
    tabs.forEach((t) => $('tab-' + t).addEventListener('click', () => showTab(t)));
    showTab(location.hash.slice(1));

    // ── API ─────────────────────────────────────────────────────────────────
    function getToken() {
        try { return sessionStorage.getItem(TOKEN_KEY); } catch { return null; }
    }
    function setToken(token) {
        try {
            if (token) sessionStorage.setItem(TOKEN_KEY, token);
            else sessionStorage.removeItem(TOKEN_KEY);
        } catch { /* storage blocked: the token only lives until reload */ }
        memoryToken = token;
    }
    let memoryToken = getToken();

    async function api(method, path, body) {
        const headers = {};
        if (memoryToken) headers.Authorization = 'Bearer ' + memoryToken;
        if (body) headers['Content-Type'] = 'application/json';
        const resp = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
        const data = await resp.json().catch(() => ({}));
        if (resp.status === 401 && path !== '/login') {
            setToken(null);
            showLogin('Session expired. Log in again.');
        }
        return { status: resp.status, ok: resp.ok, data };
    }

    function say(id, text, kind) {
        const el = $(id);
        el.textContent = text || '';
        el.className = 'msg' + (kind ? ' ' + kind : '');
    }

    // ── Login ───────────────────────────────────────────────────────────────
    function showLogin(message) {
        $('login-form').hidden = false;
        $('booking-app').hidden = true;
        $('logout').hidden = true;
        say('login-msg', message || '', message ? 'err' : '');
    }

    $('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.submitter || $('login-form').querySelector('button');
        btn.disabled = true;
        say('login-msg', 'Checking...');
        try {
            const r = await api('POST', '/login', { password: $('password').value, code: $('code').value.trim() });
            if (r.ok && r.data.token) {
                setToken(r.data.token);
                $('password').value = '';
                $('code').value = '';
                say('login-msg', '');
                await openApp();
            } else if (r.status === 429) {
                say('login-msg', `Too many tries. Locked for about ${Math.ceil((r.data.retry_after || 900) / 60)} min.`, 'err');
            } else if (r.status === 503) {
                say('login-msg', 'Admin login is not set up yet (scripts/setup_booking_admin.py).', 'err');
            } else {
                say('login-msg', 'Wrong password or code.', 'err');
                $('code').value = '';
            }
        } catch {
            say('login-msg', 'Could not reach the booking server.', 'err');
        } finally {
            btn.disabled = false;
        }
    });

    $('logout').addEventListener('click', () => {
        setToken(null);
        showLogin();
    });

    // ── Bookings and blocks ─────────────────────────────────────────────────
    let hostTz = 'America/Toronto';

    function fmt(iso, opts) {
        return new Date(iso).toLocaleString('en-CA', { timeZone: hostTz, ...opts });
    }
    function fmtRange(startIso, endIso) {
        const day = { weekday: 'short', month: 'short', day: 'numeric' };
        const time = { hour: 'numeric', minute: '2-digit' };
        const start = fmt(startIso, day) + ', ' + fmt(startIso, time);
        const sameDay = fmt(startIso, { dateStyle: 'short' }) === fmt(endIso, { dateStyle: 'short' });
        return start + ' to ' + (sameDay ? fmt(endIso, time) : fmt(endIso, day) + ', ' + fmt(endIso, time));
    }
    function wholeDays(startIso, endIso) {
        const t = { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' };
        return fmt(startIso, t) === '00:00' && fmt(endIso, t) === '00:00';
    }
    function fmtDays(startIso, endIso) {
        const day = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
        const last = new Date(new Date(endIso).getTime() - 60000).toISOString();
        const a = fmt(startIso, day), b = fmt(last, day);
        return a === b ? a + ', all day' : a + ' to ' + b;
    }

    function el(tag, props, children) {
        const node = document.createElement(tag);
        Object.assign(node, props || {});
        (children || []).forEach((c) => node.append(c));
        return node;
    }

    function renderBookings(bookings) {
        const list = $('bookings');
        list.replaceChildren();
        $('bookings-empty').hidden = bookings.length > 0;
        bookings.forEach((b) => {
            const end = new Date(new Date(b.slot_iso).getTime() + b.duration_min * 60000).toISOString();
            const who = el('div', {}, [b.name + ' ', el('a', { href: 'mailto:' + b.email, textContent: b.email })]);
            if (b.status !== 'booked') who.append(el('span', { className: 'tag', textContent: b.status }));
            const what = el('div', { className: 'what' }, [
                el('div', { className: 'when', textContent: fmtRange(b.slot_iso, end) }), who,
            ]);
            if (b.meet_link && /^https:\/\//.test(b.meet_link)) {
                what.append(el('a', { href: b.meet_link, target: '_blank', rel: 'noopener noreferrer',
                    textContent: 'Meet link', className: 'muted' }));
            }
            const cancel = el('button', { className: 'btn danger', type: 'button', textContent: 'Cancel' });
            cancel.addEventListener('click', () => cancelBooking(b, cancel));
            list.append(el('li', {}, [what, cancel]));
        });
    }

    function renderBlocks(blocks) {
        const list = $('blocks');
        list.replaceChildren();
        $('blocks-empty').hidden = blocks.length > 0;
        blocks.forEach((b) => {
            const label = wholeDays(b.start_utc, b.end_utc) ? fmtDays(b.start_utc, b.end_utc) : fmtRange(b.start_utc, b.end_utc);
            const what = el('div', { className: 'what' }, [el('div', { className: 'when', textContent: label })]);
            if (b.note) what.append(el('div', { className: 'muted', textContent: b.note }));
            const remove = el('button', { className: 'btn ghost', type: 'button', textContent: 'Remove' });
            remove.addEventListener('click', () => unblock(b, remove));
            list.append(el('li', {}, [what, remove]));
        });
    }

    async function load() {
        say('bookings-msg', 'Loading...');
        try {
            const r = await api('GET', '/bookings');
            if (!r.ok) {
                if (r.status !== 401) say('bookings-msg', 'Could not load bookings (' + r.status + ').', 'err');
                return false;
            }
            hostTz = r.data.timezone || hostTz;
            $('tz-note').textContent = 'Times are in ' + hostTz + '.';
            renderBookings(r.data.bookings || []);
            renderBlocks(r.data.blocks || []);
            say('bookings-msg', '');
            return true;
        } catch {
            say('bookings-msg', 'Could not reach the booking server.', 'err');
            return false;
        }
    }

    async function openApp() {
        $('login-form').hidden = true;
        $('booking-app').hidden = false;
        $('logout').hidden = false;
        await load();
    }

    async function cancelBooking(b, btn) {
        if (!confirm(`Cancel the call with ${b.name} (${fmt(b.slot_iso, { dateStyle: 'medium', timeStyle: 'short' })})?\n\nGoogle emails them a cancellation and the slot opens up again.`)) return;
        btn.disabled = true;
        try {
            const r = await api('POST', '/cancel', { slot_iso: b.slot_iso });
            if (r.ok) {
                say('bookings-msg', 'Cancelled. ' + b.name + ' gets an email from Google.', 'ok');
                await load();
                say('bookings-msg', 'Cancelled. ' + b.name + ' gets an email from Google.', 'ok');
            } else if (r.status !== 401) {
                say('bookings-msg', r.status === 502 ? 'Google Calendar refused, nothing changed. Check the Telegram alerts.' : 'Could not cancel (' + (r.data.error || r.status) + ').', 'err');
                btn.disabled = false;
            }
        } catch {
            say('bookings-msg', 'Could not reach the booking server.', 'err');
            btn.disabled = false;
        }
    }

    async function unblock(b, btn) {
        btn.disabled = true;
        const r = await api('POST', '/unblock', { id: b.id }).catch(() => null);
        if (r && r.ok) await load();
        else btn.disabled = false;
    }

    // ── Block form ──────────────────────────────────────────────────────────
    $('b-allday').addEventListener('change', () => { $('b-times').hidden = $('b-allday').checked; });
    $('b-start').addEventListener('change', () => {
        if (!$('b-end').value || $('b-end').value < $('b-start').value) $('b-end').value = $('b-start').value;
    });

    $('block-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const body = { start_date: $('b-start').value, end_date: $('b-end').value || $('b-start').value, note: $('b-note').value };
        if (!$('b-allday').checked) {
            body.start_time = $('b-from').value;
            body.end_time = $('b-to').value;
            if (!body.start_time || !body.end_time) { say('block-msg', 'Pick a start and end time.', 'err'); return; }
        }
        const btn = e.submitter || $('block-form').querySelector('button');
        btn.disabled = true;
        try {
            const r = await api('POST', '/block', body);
            if (r.ok) {
                $('block-form').reset();
                $('b-times').hidden = true;
                say('block-msg', 'Blocked.', 'ok');
                await load();
            } else if (r.status !== 401) {
                say('block-msg', r.data.error || 'Could not block (' + r.status + ').', 'err');
            }
        } catch {
            say('block-msg', 'Could not reach the booking server.', 'err');
        } finally {
            btn.disabled = false;
        }
    });

    if (memoryToken) openApp(); else showLogin();
})();
