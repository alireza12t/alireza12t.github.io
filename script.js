// Mobile Navigation Toggle
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

hamburger.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    hamburger.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-menu a').forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
    });
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const offset = 80;
            const targetPosition = target.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Navbar scroll effect
let lastScroll = 0;
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll <= 0) {
        navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
    }

    lastScroll = currentScroll;
});

// Intersection Observer for fade-in animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.project-card, .achievement-card, .volunteer-card, .skill-category, .timeline-item, .booking-widget').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Add active state to navigation links based on scroll position
const sections = document.querySelectorAll('section[id]');

const navHighlighter = () => {
    let scrollY = window.pageYOffset;

    sections.forEach(current => {
        const sectionHeight = current.offsetHeight;
        const sectionTop = current.offsetTop - 100;
        const sectionId = current.getAttribute('id');

        if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
            document.querySelector(`.nav-menu a[href*=${sectionId}]`)?.classList.add('active-link');
        } else {
            document.querySelector(`.nav-menu a[href*=${sectionId}]`)?.classList.remove('active-link');
        }
    });
};

window.addEventListener('scroll', navHighlighter);

// Booking Calendar with timezone support
(async function initBooking() {
    let availData;
    try {
        const resp = await fetch('availabilities.json');
        availData = resp.ok ? await resp.json() : null;
    } catch { availData = null; }
    if (!availData) return;

    const DAYS = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
    const duration = availData.meetingDurationMinutes;
    const maxDays = availData.maxBookingDaysAhead;
    const hostTz = availData.timezone; // e.g. "America/Toronto"

    // Timezone picker setup
    const COMMON_TIMEZONES = [
        'Pacific/Honolulu', 'America/Anchorage', 'America/Los_Angeles',
        'America/Denver', 'America/Chicago', 'America/New_York',
        'America/Toronto', 'America/Halifax', 'America/St_Johns',
        'America/Sao_Paulo', 'Atlantic/Reykjavik', 'Europe/London',
        'Europe/Paris', 'Europe/Berlin', 'Europe/Helsinki',
        'Europe/Istanbul', 'Asia/Dubai', 'Asia/Kolkata',
        'Asia/Bangkok', 'Asia/Shanghai', 'Asia/Tokyo',
        'Asia/Seoul', 'Australia/Sydney', 'Pacific/Auckland',
    ];

    const tzSelect = document.getElementById('tz-select');
    const guessedTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    let visitorTz = guessedTz;

    // Build timezone dropdown — ensure visitor's detected tz is included
    const tzSet = new Set(COMMON_TIMEZONES);
    tzSet.add(guessedTz);
    const sortedTzs = [...tzSet].sort();

    function tzLabel(tz) {
        try {
            const now = new Date();
            const short = now.toLocaleString('en-US', { timeZone: tz, timeZoneName: 'short' }).split(' ').pop();
            const offset = now.toLocaleString('en-US', { timeZone: tz, timeZoneName: 'longOffset' }).split('GMT').pop() || '+0';
            return `(GMT${offset}) ${tz.replace(/_/g, ' ')} — ${short}`;
        } catch {
            return tz;
        }
    }

    for (const tz of sortedTzs) {
        const opt = document.createElement('option');
        opt.value = tz;
        opt.textContent = tzLabel(tz);
        if (tz === guessedTz) opt.selected = true;
        tzSelect.appendChild(opt);
    }

    tzSelect.addEventListener('change', () => {
        visitorTz = tzSelect.value;
        selectedDate = null;
        selectedSlot = null;
        renderCalendar();
        slotsPanel.innerHTML = '<div class="slots-placeholder"><i class="fas fa-calendar-check"></i><p>Select a date to see available times</p></div>';
    });

    let currentMonth, currentYear, selectedDate = null, selectedSlot = null;

    const calDays = document.getElementById('cal-days');
    const calMonthYear = document.getElementById('cal-month-year');
    const slotsPanel = document.getElementById('booking-slots');

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    currentMonth = today.getMonth();
    currentYear = today.getFullYear();

    const maxDate = new Date(today);
    maxDate.setDate(maxDate.getDate() + maxDays);

    function toMinutes(timeStr) {
        const [h, m] = timeStr.split(':').map(Number);
        return h * 60 + m;
    }

    function formatTimeInTz(date, tz) {
        return date.toLocaleTimeString('en-US', {
            timeZone: tz, hour: 'numeric', minute: '2-digit', hour12: true
        });
    }

    // Build a Date object for a given date string + time (minutes) in a given timezone
    function dateInTz(dateStr, minutes, tz) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        // Create an ISO-ish string and use the timezone to interpret it
        const isoish = `${dateStr}T${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:00`;
        // Get the UTC equivalent by computing offset
        const dummy = new Date(isoish + 'Z'); // treat as UTC first
        const utcStr = dummy.toLocaleString('en-US', { timeZone: tz });
        const inTz = new Date(utcStr);
        const offset = dummy.getTime() - inTz.getTime();
        return new Date(dummy.getTime() + offset);
    }

    // Get available slots for a visitor-local date, converting from host timezone
    function getAvailableSlots(visitorDate) {
        const visitorDateStr = visitorDate.toISOString().slice(0, 10);
        const slots = [];

        // Check host-tz dates that could map to this visitor date (check day before, same, day after)
        for (let dayOffset = -1; dayOffset <= 1; dayOffset++) {
            const hostDate = new Date(visitorDate);
            hostDate.setDate(hostDate.getDate() + dayOffset);
            const hostDateStr = hostDate.toISOString().slice(0, 10);
            const dayName = DAYS[hostDate.getDay()];
            const windows = availData.weeklyAvailability[dayName];
            if (!windows || windows.length === 0) continue;

            const blocked = (availData.blockedSlots || [])
                .filter(b => b.date === hostDateStr)
                .map(b => ({ start: toMinutes(b.start), end: toMinutes(b.end) }));

            for (const w of windows) {
                let cursor = toMinutes(w.start);
                const end = toMinutes(w.end);
                while (cursor + duration <= end) {
                    const slotStart = cursor;
                    const slotEnd = cursor + duration;
                    const isBlocked = blocked.some(b => slotStart < b.end && slotEnd > b.start);
                    if (!isBlocked) {
                        // Convert host-tz slot to absolute time, then to visitor-tz
                        const absStart = dateInTz(hostDateStr, slotStart, hostTz);
                        const absEnd = dateInTz(hostDateStr, slotEnd, hostTz);

                        // Check if this slot falls on the visitor's selected date
                        const visitorStart = new Date(absStart.toLocaleString('en-US', { timeZone: visitorTz }));
                        const slotVisitorDate = `${visitorStart.getFullYear()}-${String(visitorStart.getMonth()+1).padStart(2,'0')}-${String(visitorStart.getDate()).padStart(2,'0')}`;

                        if (slotVisitorDate === visitorDateStr) {
                            // Skip past slots
                            if (absStart <= new Date()) { cursor += duration; continue; }

                            slots.push({
                                absStart,
                                absEnd,
                                label: `${formatTimeInTz(absStart, visitorTz)} - ${formatTimeInTz(absEnd, visitorTz)}`,
                                hostDate: hostDateStr,
                                hostStart: slotStart,
                                hostEnd: slotEnd,
                            });
                        }
                    }
                    cursor += duration;
                }
            }
        }

        // Sort by absolute time and deduplicate
        slots.sort((a, b) => a.absStart - b.absStart);
        return slots;
    }

    function isDayAvailable(date) {
        if (date < today || date > maxDate) return false;
        return getAvailableSlots(date).length > 0;
    }

    function renderCalendar() {
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'];
        calMonthYear.textContent = `${monthNames[currentMonth]} ${currentYear}`;

        const firstDay = new Date(currentYear, currentMonth, 1).getDay();
        const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

        calDays.innerHTML = '';
        for (let i = 0; i < firstDay; i++) {
            calDays.appendChild(document.createElement('div'));
        }

        for (let d = 1; d <= daysInMonth; d++) {
            const date = new Date(currentYear, currentMonth, d);
            const el = document.createElement('div');
            el.className = 'cal-day';
            el.textContent = d;

            if (date.getTime() === today.getTime()) el.classList.add('today');

            if (isDayAvailable(date)) {
                el.classList.add('available');
                el.addEventListener('click', () => selectDate(date));
            }

            if (selectedDate && date.getTime() === selectedDate.getTime()) {
                el.classList.add('selected');
            }

            calDays.appendChild(el);
        }
    }

    function selectDate(date) {
        selectedDate = date;
        selectedSlot = null;
        renderCalendar();
        renderSlots(date);
    }

    function renderSlots(date) {
        const slots = getAvailableSlots(date);
        const dateLabel = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

        if (slots.length === 0) {
            slotsPanel.innerHTML = '<div class="no-slots"><i class="fas fa-moon"></i>No available slots on this day</div>';
            return;
        }

        let html = `<div class="slots-header">${dateLabel}</div>`;
        for (let i = 0; i < slots.length; i++) {
            html += `<button class="slot-btn" data-idx="${i}">${slots[i].label}</button>`;
        }
        slotsPanel.innerHTML = html;

        slotsPanel.querySelectorAll('.slot-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                slotsPanel.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                selectedSlot = slots[+btn.dataset.idx];

                let confirmDiv = slotsPanel.querySelector('.booking-confirm');
                if (!confirmDiv) {
                    confirmDiv = document.createElement('div');
                    confirmDiv.className = 'booking-confirm';
                    confirmDiv.innerHTML = '<button class="confirm-btn">Confirm & Send Request</button>';
                    slotsPanel.appendChild(confirmDiv);
                    confirmDiv.querySelector('.confirm-btn').addEventListener('click', confirmBooking);
                }
            });
        });
    }

    function confirmBooking() {
        if (!selectedDate || !selectedSlot) return;
        const dateStr = selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
        const timeStr = selectedSlot.label;
        const tzShort = visitorTz.replace(/_/g, ' ');
        const subject = encodeURIComponent(`Meeting Request — ${dateStr}`);
        const body = encodeURIComponent(
            `Hi Alireza,\n\nI'd like to book a call with you:\n\nDate: ${dateStr}\nTime: ${timeStr} (${tzShort})\n\nPlease let me know if this works!\n\nBest regards`
        );
        window.location.href = `mailto:${availData.contactEmail}?subject=${subject}&body=${body}`;
    }

    document.getElementById('cal-prev').addEventListener('click', () => {
        currentMonth--;
        if (currentMonth < 0) { currentMonth = 11; currentYear--; }
        renderCalendar();
    });
    document.getElementById('cal-next').addEventListener('click', () => {
        currentMonth++;
        if (currentMonth > 11) { currentMonth = 0; currentYear++; }
        renderCalendar();
    });

    renderCalendar();
})();

// Add CSS for active link
const style = document.createElement('style');
style.textContent = `
    .nav-menu a.active-link {
        color: var(--primary-color);
        position: relative;
    }
    .nav-menu a.active-link::after {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 0;
        width: 100%;
        height: 2px;
        background-color: var(--primary-color);
    }
`;
document.head.appendChild(style);
