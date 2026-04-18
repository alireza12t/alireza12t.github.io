// ===== Dark Mode Toggle =====
(function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
})();

document.getElementById('theme-toggle').addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon();
});

function updateThemeIcon() {
    const icon = document.querySelector('#theme-toggle i');
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
}
updateThemeIcon();

// ===== Multi-language (EN/FR) =====
const translations = {
    en: {
        nav_home: 'Home',
        nav_about: 'About',
        nav_experience: 'Experience',
        nav_education: 'Education',
        nav_projects: 'Projects',
        nav_skills: 'Skills',
        nav_contact: 'Contact',
        nav_booking: 'Book a Call',
        hero_title: 'Hi, I\'m <span class="highlight">Alireza Toghiani</span>',
        hero_subtitle: 'Senior iOS Engineer',
        hero_description: 'Passionate about creating innovative mobile solutions with 6+ years of experience in iOS development',
        hero_cta_primary: 'Get In Touch',
        hero_cta_secondary: 'View My Work',
        about_title: 'About Me',
        about_p1: 'iOS Engineer with 6+ years of experience, passionate about transforming app ideas into reality for the betterment of daily life.',
        about_p2: 'Led iOS development team to launch 7 successful apps while collaborating with internal team leads and external partners in fast-paced environments.',
        about_p3: 'Academic foundation in security principles and cryptographic systems from master\'s studies.',
        about_location: 'Montreal, QC, Canada',
        about_degree: 'M.Sc. Information Systems Security, Concordia University',
        about_role: 'Senior iOS Engineer',
        exp_title: 'Experience',
        achievements_title: 'Achievements & Honors',
        achievement_silver: 'Silver Medal',
        achievement_silver_desc: 'Mobile Application Development<br>WorldSkills Asia 2021',
        achievement_clean: 'Clean Solution Nomination',
        achievement_clean_desc: 'WorldSkills Asia 2021',
        edu_title: 'Education',
        projects_title: 'Featured Projects',
        project_arscanner: 'ARScanner',
        project_arscanner_desc: 'AR 3D modeling application leveraging ARKit to create immersive augmented reality experiences.',
        project_dailydiet: 'DailyDiet',
        project_dailydiet_desc: 'Nutrition planning iOS app helping users track their diet and achieve their health goals.',
        project_tedx: 'TEDxTehran iOS App',
        project_tedx_desc: 'Open-source iOS application for TEDxTehran, providing access to talks and event information.',
        skills_title: 'Skills & Technologies',
        skills_languages: '<i class="fas fa-code"></i> Languages & Frameworks',
        skills_tools: '<i class="fas fa-tools"></i> Tools & Platforms',
        skills_design: '<i class="fas fa-palette"></i> Design & Architecture',
        skills_spoken: '<i class="fas fa-globe"></i> Languages',
        lang_english: 'English (Professional)',
        lang_persian: 'Persian (Native)',
        lang_french: 'French (Basic)',
        community_title: 'Community Involvement',
        volunteer_vp: 'Vice President & Lead of App Developement',
        volunteer_vp_org: 'AtHackCTF - Concordia Cyber Security Hackathon',
        volunteer_marketing: 'Lead of Marketing',
        volunteer_marketing_org: 'AtHackCTF - Concordia Cyber Security Hackathon',
        volunteer_instructor: 'iOS Instructor',
        volunteer_instructor_org: 'CS50x Iran',
        contact_title: 'Get In Touch',
        contact_description: 'I\'m always interested in hearing about new opportunities, collaborations, or just chatting about iOS development. Feel free to reach out!',
        contact_linkedin: 'Connect with me professionally',
        contact_github: 'Check out my code',
        contact_email_label: 'Email',
        contact_phone_label: 'Phone',
        booking_title: 'Book a Call',
        booking_description: 'Pick a time that works for you and let\'s chat!',
        booking_placeholder: 'Select a date to see available times',
        cal_sun: 'Sun', cal_mon: 'Mon', cal_tue: 'Tue', cal_wed: 'Wed',
        cal_thu: 'Thu', cal_fri: 'Fri', cal_sat: 'Sat',
        footer_copyright: '&copy; 2025 Alireza Toghiani Khorasgani. All rights reserved.',
        footer_built: 'Built with <i class="fas fa-heart"></i> in Montreal',
    },
    fr: {
        nav_home: 'Accueil',
        nav_about: '\u00C0 propos',
        nav_experience: 'Exp\u00E9rience',
        nav_education: 'Formation',
        nav_projects: 'Projets',
        nav_skills: 'Comp\u00E9tences',
        nav_contact: 'Contact',
        nav_booking: 'R\u00E9server un appel',
        hero_title: 'Bonjour, je suis <span class="highlight">Alireza Toghiani</span>',
        hero_subtitle: 'Ing\u00E9nieur iOS Senior',
        hero_description: 'Passionn\u00E9 par la cr\u00E9ation de solutions mobiles innovantes avec plus de 6 ans d\u2019exp\u00E9rience en d\u00E9veloppement iOS',
        hero_cta_primary: 'Me contacter',
        hero_cta_secondary: 'Voir mes projets',
        about_title: '\u00C0 propos de moi',
        about_p1: 'Ing\u00E9nieur iOS avec plus de 6 ans d\u2019exp\u00E9rience, passionn\u00E9 par la transformation d\u2019id\u00E9es d\u2019applications en r\u00E9alit\u00E9 pour am\u00E9liorer le quotidien.',
        about_p2: 'J\u2019ai dirig\u00E9 une \u00E9quipe de d\u00E9veloppement iOS pour lancer 7 applications r\u00E9ussies en collaborant avec des responsables internes et des partenaires externes dans des environnements dynamiques.',
        about_p3: 'Formation acad\u00E9mique en principes de s\u00E9curit\u00E9 et syst\u00E8mes cryptographiques acquise lors de mes \u00E9tudes de ma\u00EEtrise.',
        about_location: 'Montr\u00E9al, QC, Canada',
        about_degree: 'M.Sc. S\u00E9curit\u00E9 des syst\u00E8mes d\u2019information, Universit\u00E9 Concordia',
        about_role: 'Ing\u00E9nieur iOS Senior',
        exp_title: 'Exp\u00E9rience',
        achievements_title: 'Distinctions et r\u00E9compenses',
        achievement_silver: 'M\u00E9daille d\u2019argent',
        achievement_silver_desc: 'D\u00E9veloppement d\u2019applications mobiles<br>WorldSkills Asia 2021',
        achievement_clean: 'Nomination pour la solution la plus propre',
        achievement_clean_desc: 'WorldSkills Asia 2021',
        edu_title: 'Formation',
        projects_title: 'Projets en vedette',
        project_arscanner: 'ARScanner',
        project_arscanner_desc: 'Application de mod\u00E9lisation 3D en r\u00E9alit\u00E9 augment\u00E9e utilisant ARKit pour cr\u00E9er des exp\u00E9riences immersives.',
        project_dailydiet: 'DailyDiet',
        project_dailydiet_desc: 'Application iOS de planification nutritionnelle aidant les utilisateurs \u00E0 suivre leur alimentation et atteindre leurs objectifs de sant\u00E9.',
        project_tedx: 'Application iOS TEDxTehran',
        project_tedx_desc: 'Application iOS open source pour TEDxTehran, offrant un acc\u00E8s aux conf\u00E9rences et aux informations sur les \u00E9v\u00E9nements.',
        skills_title: 'Comp\u00E9tences et technologies',
        skills_languages: '<i class="fas fa-code"></i> Langages et frameworks',
        skills_tools: '<i class="fas fa-tools"></i> Outils et plateformes',
        skills_design: '<i class="fas fa-palette"></i> Design et architecture',
        skills_spoken: '<i class="fas fa-globe"></i> Langues',
        lang_english: 'Anglais (professionnel)',
        lang_persian: 'Persan (langue maternelle)',
        lang_french: 'Fran\u00E7ais (notions)',
        community_title: 'Implication communautaire',
        volunteer_vp: 'Vice-pr\u00E9sident et responsable du d\u00E9veloppement d\u2019applications',
        volunteer_vp_org: 'AtHackCTF - Hackathon de cybers\u00E9curit\u00E9 de Concordia',
        volunteer_marketing: 'Responsable du marketing',
        volunteer_marketing_org: 'AtHackCTF - Hackathon de cybers\u00E9curit\u00E9 de Concordia',
        volunteer_instructor: 'Instructeur iOS',
        volunteer_instructor_org: 'CS50x Iran',
        contact_title: 'Me contacter',
        contact_description: 'Je suis toujours ouvert aux nouvelles opportunit\u00E9s, collaborations ou simplement \u00E0 discuter de d\u00E9veloppement iOS. N\u2019h\u00E9sitez pas \u00E0 me contacter\u00A0!',
        contact_linkedin: 'Connectez-vous avec moi',
        contact_github: 'D\u00E9couvrez mon code',
        contact_email_label: 'Courriel',
        contact_phone_label: 'T\u00E9l\u00E9phone',
        booking_title: 'R\u00E9server un appel',
        booking_description: 'Choisissez un cr\u00E9neau qui vous convient et discutons\u00A0!',
        booking_placeholder: 'S\u00E9lectionnez une date pour voir les cr\u00E9neaux disponibles',
        cal_sun: 'Dim', cal_mon: 'Lun', cal_tue: 'Mar', cal_wed: 'Mer',
        cal_thu: 'Jeu', cal_fri: 'Ven', cal_sat: 'Sam',
        footer_copyright: '&copy; 2025 Alireza Toghiani Khorasgani. Tous droits r\u00E9serv\u00E9s.',
        footer_built: 'Con\u00E7u avec <i class="fas fa-heart"></i> \u00E0 Montr\u00E9al',
    }
};

function getCurrentLang() {
    return localStorage.getItem('lang') || 'en';
}

function applyTranslations(lang) {
    const t = translations[lang];
    if (!t) return;

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key] !== undefined) {
            el.textContent = t[key];
        }
    });

    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        if (t[key] !== undefined) {
            el.innerHTML = t[key];
        }
    });

    // Update lang toggle button flag+text to show the OTHER language
    const langBtn = document.getElementById('lang-toggle');
    langBtn.innerHTML = lang === 'en' ? '<span class="flag-icon">🇫🇷</span> FR' : '<span class="flag-icon">🇬🇧</span> EN';

    document.documentElement.setAttribute('lang', lang);
}

document.getElementById('lang-toggle').addEventListener('click', () => {
    const current = getCurrentLang();
    const next = current === 'en' ? 'fr' : 'en';
    localStorage.setItem('lang', next);
    applyTranslations(next);
});

// Apply saved language on load
applyTranslations(getCurrentLang());

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
    const BOOKING_API_URL = 'https://r7n6gzfefcwld37lyjkabauqk40sqydj.lambda-url.us-east-1.on.aws/';

    let availData;
    try {
        const resp = await fetch('availabilities.json');
        availData = resp.ok ? await resp.json() : null;
    } catch { availData = null; }
    if (!availData) return;

    // Fetch already-booked slots from Lambda so we can hide them
    let bookedSlots = new Set();
    if (BOOKING_API_URL) {
        try {
            const r = await fetch(BOOKING_API_URL);
            if (r.ok) {
                const data = await r.json();
                (data.booked_slots || []).forEach(s => bookedSlots.add(s));
            }
        } catch { /* Lambda not deployed yet — show all slots */ }
    }

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

    // Build a Date (UTC instant) for a given date string + time (minutes) in a given timezone
    function dateInTz(dateStr, minutes, tz) {
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        // Treat as UTC first to get a reference point
        const utcGuess = new Date(`${dateStr}T${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:00Z`);
        // Format that UTC instant in the target timezone to find the offset
        const parts = {};
        new Intl.DateTimeFormat('en-US', {
            timeZone: tz, hour12: false,
            year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit'
        }).formatToParts(utcGuess).forEach(p => parts[p.type] = p.value);
        const tzH = parseInt(parts.hour === '24' ? '0' : parts.hour);
        const tzM = parseInt(parts.minute);
        const tzDay = parseInt(parts.day);
        const guessDay = utcGuess.getUTCDate();
        // Offset in minutes: how far ahead is tz from UTC
        let offsetMin = (tzH * 60 + tzM) - (h * 60 + m) + (tzDay - guessDay) * 1440;
        if (offsetMin > 720) offsetMin -= 1440;
        if (offsetMin < -720) offsetMin += 1440;
        // Actual UTC time = desired local time - offset
        return new Date(utcGuess.getTime() - offsetMin * 60000);
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
                        const vParts = {};
                        new Intl.DateTimeFormat('en-CA', {
                            timeZone: visitorTz, year: 'numeric', month: '2-digit', day: '2-digit'
                        }).formatToParts(absStart).forEach(p => vParts[p.type] = p.value);
                        const slotVisitorDate = `${vParts.year}-${vParts.month}-${vParts.day}`;

                        if (slotVisitorDate === visitorDateStr) {
                            // Skip past slots
                            if (absStart <= new Date()) { cursor += duration; continue; }
                            // Skip already-booked slots
                            if (bookedSlots.has(absStart.toISOString())) { cursor += duration; continue; }

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
                    confirmDiv.innerHTML = `
                        <input type="text" id="booking-name" class="booking-input" placeholder="Your name" required>
                        <input type="email" id="booking-email" class="booking-input" placeholder="Your email" required>
                        <button class="confirm-btn">Confirm & Send Invite</button>`;
                    slotsPanel.appendChild(confirmDiv);
                    confirmDiv.querySelector('.confirm-btn').addEventListener('click', confirmBooking);
                }
            });
        });
    }

    async function confirmBooking() {
        if (!selectedDate || !selectedSlot) return;
        const nameInput = document.getElementById('booking-name');
        const emailInput = document.getElementById('booking-email');
        const confirmBtn = slotsPanel.querySelector('.confirm-btn');
        const name = nameInput.value.trim();
        const email = emailInput.value.trim();
        if (!name) { nameInput.focus(); return; }
        if (!email || !email.includes('@')) { emailInput.focus(); return; }

        if (!BOOKING_API_URL) {
            alert('Booking is not available yet. Please try again later.');
            return;
        }

        // Loading state
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Booking...';

        try {
            const resp = await fetch(BOOKING_API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    slot_iso: selectedSlot.absStart.toISOString(),
                    duration_min: duration,
                    name,
                    email,
                }),
            });
            const data = await resp.json();

            if (resp.status === 409) {
                // Slot was taken — mark it booked and refresh
                bookedSlots.add(selectedSlot.absStart.toISOString());
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Confirm & Send Invite';
                slotsPanel.querySelector('.booking-confirm').remove();
                selectedSlot = null;
                renderSlots(selectedDate);
                const errDiv = document.createElement('div');
                errDiv.className = 'booking-error';
                errDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> That slot was just taken. Please pick another time.';
                slotsPanel.prepend(errDiv);
                setTimeout(() => errDiv.remove(), 5000);
                return;
            }

            if (!resp.ok) {
                throw new Error(data.error || 'Booking failed');
            }

            // Success — show confirmation
            bookedSlots.add(selectedSlot.absStart.toISOString());
            const dateStr = selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
            const timeStr = selectedSlot.label;
            const meetLink = data.meet_link;

            slotsPanel.innerHTML = `
                <div class="booking-success">
                    <i class="fas fa-check-circle"></i>
                    <h3>Booking Confirmed!</h3>
                    <p><strong>${dateStr}</strong><br>${timeStr}</p>
                    <p>A calendar invite has been sent to <strong>${email}</strong>.</p>
                    ${meetLink ? `<a href="${meetLink}" target="_blank" class="meet-link"><i class="fas fa-video"></i> Join Google Meet</a>` : ''}
                    <button class="confirm-btn" onclick="location.reload()">Book Another</button>
                </div>`;
        } catch (err) {
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Confirm & Send Invite';
            const errDiv = document.createElement('div');
            errDiv.className = 'booking-error';
            errDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${err.message}. Please try again.`;
            slotsPanel.querySelector('.booking-confirm').prepend(errDiv);
            setTimeout(() => errDiv.remove(), 5000);
        }
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
