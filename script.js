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
        booking_step_date: 'Select Date',
        booking_step_time: 'Choose Time',
        booking_step_confirm: 'Confirm',
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
        booking_step_date: 'Choisir la date',
        booking_step_time: 'Choisir l\u2019heure',
        booking_step_confirm: 'Confirmer',
        footer_copyright: '&copy; 2025 Alireza Toghiani Khorasgani. Tous droits r\u00E9serv\u00E9s.',
        footer_built: 'Con\u00E7u avec <i class="fas fa-heart"></i> \u00E0 Montr\u00E9al',
    },
    fa: {
        nav_home: '\u062E\u0627\u0646\u0647',
        nav_about: '\u062F\u0631\u0628\u0627\u0631\u0647 \u0645\u0646',
        nav_experience: '\u062A\u062C\u0631\u0628\u0647',
        nav_education: '\u062A\u062D\u0635\u06CC\u0644\u0627\u062A',
        nav_projects: '\u067E\u0631\u0648\u0698\u0647\u200C\u0647\u0627',
        nav_skills: '\u0645\u0647\u0627\u0631\u062A\u200C\u0647\u0627',
        nav_contact: '\u062A\u0645\u0627\u0633',
        nav_booking: '\u0631\u0632\u0631\u0648 \u062A\u0645\u0627\u0633',
        hero_title: '\u0633\u0644\u0627\u0645\u060C \u0645\u0646 <span class="highlight">\u0639\u0644\u06CC\u0631\u0636\u0627 \u062A\u0642\u06CC\u0627\u0646\u06CC</span> \u0647\u0633\u062A\u0645',
        hero_subtitle: '\u0645\u0647\u0646\u062F\u0633 \u0627\u0631\u0634\u062F iOS',
        hero_description: '\u0639\u0644\u0627\u0642\u0647\u200C\u0645\u0646\u062F \u0628\u0647 \u062E\u0644\u0642 \u0631\u0627\u0647\u200C\u062D\u0644\u200C\u0647\u0627\u06CC \u0646\u0648\u0622\u0648\u0631\u0627\u0646\u0647 \u0645\u0648\u0628\u0627\u06CC\u0644 \u0628\u0627 \u0628\u06CC\u0634 \u0627\u0632 \u06F6 \u0633\u0627\u0644 \u062A\u062C\u0631\u0628\u0647 \u062F\u0631 \u062A\u0648\u0633\u0639\u0647 iOS',
        hero_cta_primary: '\u062A\u0645\u0627\u0633 \u0628\u0627 \u0645\u0646',
        hero_cta_secondary: '\u0645\u0634\u0627\u0647\u062F\u0647 \u06A9\u0627\u0631\u0647\u0627\u06CC \u0645\u0646',
        about_title: '\u062F\u0631\u0628\u0627\u0631\u0647 \u0645\u0646',
        about_p1: '\u0645\u0647\u0646\u062F\u0633 iOS \u0628\u0627 \u0628\u06CC\u0634 \u0627\u0632 \u06F6 \u0633\u0627\u0644 \u062A\u062C\u0631\u0628\u0647\u060C \u0639\u0644\u0627\u0642\u0647\u200C\u0645\u0646\u062F \u0628\u0647 \u062A\u0628\u062F\u06CC\u0644 \u0627\u06CC\u062F\u0647\u200C\u0647\u0627\u06CC \u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 \u0628\u0647 \u0648\u0627\u0642\u0639\u06CC\u062A \u0628\u0631\u0627\u06CC \u0628\u0647\u0628\u0648\u062F \u0632\u0646\u062F\u06AF\u06CC \u0631\u0648\u0632\u0645\u0631\u0647.',
        about_p2: '\u0631\u0647\u0628\u0631\u06CC \u062A\u06CC\u0645 \u062A\u0648\u0633\u0639\u0647 iOS \u0628\u0631\u0627\u06CC \u0627\u0646\u062A\u0634\u0627\u0631 \u06F7 \u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 \u0645\u0648\u0641\u0642 \u0628\u0627 \u0647\u0645\u06A9\u0627\u0631\u06CC \u062A\u06CC\u0645\u200C\u0647\u0627\u06CC \u062F\u0627\u062E\u0644\u06CC \u0648 \u0634\u0631\u06A9\u0627\u06CC \u062E\u0627\u0631\u062C\u06CC.',
        about_p3: '\u067E\u0627\u06CC\u0647 \u0622\u06A9\u0627\u062F\u0645\u06CC\u06A9 \u062F\u0631 \u0627\u0635\u0648\u0644 \u0627\u0645\u0646\u06CC\u062A \u0648 \u0633\u06CC\u0633\u062A\u0645\u200C\u0647\u0627\u06CC \u0631\u0645\u0632\u0646\u06AF\u0627\u0631\u06CC \u0627\u0632 \u062F\u0648\u0631\u0647 \u06A9\u0627\u0631\u0634\u0646\u0627\u0633\u06CC \u0627\u0631\u0634\u062F.',
        about_location: '\u0645\u0648\u0646\u062A\u0631\u0627\u0644\u060C \u06A9\u0628\u06A9\u060C \u06A9\u0627\u0646\u0627\u062F\u0627',
        about_degree: '\u06A9\u0627\u0631\u0634\u0646\u0627\u0633\u06CC \u0627\u0631\u0634\u062F \u0627\u0645\u0646\u06CC\u062A \u0633\u06CC\u0633\u062A\u0645\u200C\u0647\u0627\u06CC \u0627\u0637\u0644\u0627\u0639\u0627\u062A\u06CC\u060C \u062F\u0627\u0646\u0634\u06AF\u0627\u0647 \u06A9\u0627\u0646\u06A9\u0648\u0631\u062F\u06CC\u0627',
        about_role: '\u0645\u0647\u0646\u062F\u0633 \u0627\u0631\u0634\u062F iOS',
        exp_title: '\u062A\u062C\u0631\u0628\u0647 \u06A9\u0627\u0631\u06CC',
        achievements_title: '\u0627\u0641\u062A\u062E\u0627\u0631\u0627\u062A \u0648 \u062C\u0648\u0627\u06CC\u0632',
        achievement_silver: '\u0645\u062F\u0627\u0644 \u0646\u0642\u0631\u0647',
        achievement_silver_desc: '\u062A\u0648\u0633\u0639\u0647 \u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 \u0645\u0648\u0628\u0627\u06CC\u0644<br>WorldSkills Asia 2021',
        achievement_clean: '\u0646\u0627\u0645\u0632\u062F \u062A\u0645\u06CC\u0632\u062A\u0631\u06CC\u0646 \u0631\u0627\u0647\u200C\u062D\u0644',
        achievement_clean_desc: 'WorldSkills Asia 2021',
        edu_title: '\u062A\u062D\u0635\u06CC\u0644\u0627\u062A',
        projects_title: '\u067E\u0631\u0648\u0698\u0647\u200C\u0647\u0627\u06CC \u0628\u0631\u062C\u0633\u062A\u0647',
        project_arscanner: 'ARScanner',
        project_arscanner_desc: '\u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 \u0645\u062F\u0644\u200C\u0633\u0627\u0632\u06CC \u0633\u0647\u200C\u0628\u0639\u062F\u06CC AR \u0628\u0627 \u0627\u0633\u062A\u0641\u0627\u062F\u0647 \u0627\u0632 ARKit \u0628\u0631\u0627\u06CC \u062A\u062C\u0631\u0628\u0647\u200C\u0647\u0627\u06CC \u0648\u0627\u0642\u0639\u06CC\u062A \u0627\u0641\u0632\u0648\u062F\u0647.',
        project_dailydiet: 'DailyDiet',
        project_dailydiet_desc: '\u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 \u0628\u0631\u0646\u0627\u0645\u0647\u200C\u0631\u06CC\u0632\u06CC \u062A\u063A\u0630\u06CC\u0647 \u0628\u0631\u0627\u06CC \u06A9\u0645\u06A9 \u0628\u0647 \u06A9\u0627\u0631\u0628\u0631\u0627\u0646 \u062F\u0631 \u067E\u06CC\u06AF\u06CC\u0631\u06CC \u0631\u0698\u06CC\u0645 \u063A\u0630\u0627\u06CC\u06CC.',
        project_tedx: '\u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 iOS TEDx\u062A\u0647\u0631\u0627\u0646',
        project_tedx_desc: '\u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646 \u0645\u062A\u0646\u200C\u0628\u0627\u0632 iOS \u0628\u0631\u0627\u06CC TEDx\u062A\u0647\u0631\u0627\u0646\u060C \u062F\u0633\u062A\u0631\u0633\u06CC \u0628\u0647 \u0633\u062E\u0646\u0631\u0627\u0646\u06CC\u200C\u0647\u0627 \u0648 \u0627\u0637\u0644\u0627\u0639\u0627\u062A \u0631\u0648\u06CC\u062F\u0627\u062F\u0647\u0627.',
        skills_title: '\u0645\u0647\u0627\u0631\u062A\u200C\u0647\u0627 \u0648 \u062A\u06A9\u0646\u0648\u0644\u0648\u0698\u06CC\u200C\u0647\u0627',
        skills_languages: '<i class="fas fa-code"></i> \u0632\u0628\u0627\u0646\u200C\u0647\u0627 \u0648 \u0641\u0631\u06CC\u0645\u0648\u0631\u06A9\u200C\u0647\u0627',
        skills_tools: '<i class="fas fa-tools"></i> \u0627\u0628\u0632\u0627\u0631\u0647\u0627 \u0648 \u067E\u0644\u062A\u0641\u0631\u0645\u200C\u0647\u0627',
        skills_design: '<i class="fas fa-palette"></i> \u0637\u0631\u0627\u062D\u06CC \u0648 \u0645\u0639\u0645\u0627\u0631\u06CC',
        skills_spoken: '<i class="fas fa-globe"></i> \u0632\u0628\u0627\u0646\u200C\u0647\u0627',
        lang_english: '\u0627\u0646\u06AF\u0644\u06CC\u0633\u06CC (\u062D\u0631\u0641\u0647\u200C\u0627\u06CC)',
        lang_persian: '\u0641\u0627\u0631\u0633\u06CC (\u0632\u0628\u0627\u0646 \u0645\u0627\u062F\u0631\u06CC)',
        lang_french: '\u0641\u0631\u0627\u0646\u0633\u0647 (\u0645\u0642\u062F\u0645\u0627\u062A\u06CC)',
        community_title: '\u0641\u0639\u0627\u0644\u06CC\u062A\u200C\u0647\u0627\u06CC \u0627\u062C\u062A\u0645\u0627\u0639\u06CC',
        volunteer_vp: '\u0646\u0627\u06CC\u0628 \u0631\u0626\u06CC\u0633 \u0648 \u0645\u0633\u0626\u0648\u0644 \u062A\u0648\u0633\u0639\u0647 \u0627\u067E\u0644\u06CC\u06A9\u06CC\u0634\u0646',
        volunteer_vp_org: 'AtHackCTF - \u0647\u06A9\u0627\u062A\u0648\u0646 \u0627\u0645\u0646\u06CC\u062A \u0633\u0627\u06CC\u0628\u0631\u06CC \u06A9\u0627\u0646\u06A9\u0648\u0631\u062F\u06CC\u0627',
        volunteer_marketing: '\u0645\u0633\u0626\u0648\u0644 \u0628\u0627\u0632\u0627\u0631\u06CC\u0627\u0628\u06CC',
        volunteer_marketing_org: 'AtHackCTF - \u0647\u06A9\u0627\u062A\u0648\u0646 \u0627\u0645\u0646\u06CC\u062A \u0633\u0627\u06CC\u0628\u0631\u06CC \u06A9\u0627\u0646\u06A9\u0648\u0631\u062F\u06CC\u0627',
        volunteer_instructor: '\u0645\u062F\u0631\u0633 iOS',
        volunteer_instructor_org: 'CS50x \u0627\u06CC\u0631\u0627\u0646',
        contact_title: '\u062A\u0645\u0627\u0633 \u0628\u0627 \u0645\u0646',
        contact_description: '\u0647\u0645\u06CC\u0634\u0647 \u0639\u0644\u0627\u0642\u0647\u200C\u0645\u0646\u062F \u0628\u0647 \u0634\u0646\u06CC\u062F\u0646 \u0641\u0631\u0635\u062A\u200C\u0647\u0627\u06CC \u062C\u062F\u06CC\u062F\u060C \u0647\u0645\u06A9\u0627\u0631\u06CC\u200C\u0647\u0627 \u06CC\u0627 \u06AF\u0641\u062A\u06AF\u0648 \u062F\u0631\u0628\u0627\u0631\u0647 \u062A\u0648\u0633\u0639\u0647 iOS \u0647\u0633\u062A\u0645. \u062E\u0648\u0634\u062D\u0627\u0644 \u0645\u06CC\u200C\u0634\u0645 \u0628\u0627 \u0645\u0646 \u062A\u0645\u0627\u0633 \u0628\u06AF\u06CC\u0631\u06CC\u062F!',
        contact_linkedin: '\u0627\u0631\u062A\u0628\u0627\u0637 \u062D\u0631\u0641\u0647\u200C\u0627\u06CC',
        contact_github: '\u06A9\u062F\u0647\u0627\u06CC \u0645\u0646 \u0631\u0627 \u0628\u0628\u06CC\u0646\u06CC\u062F',
        contact_email_label: '\u0627\u06CC\u0645\u06CC\u0644',
        contact_phone_label: '\u062A\u0644\u0641\u0646',
        booking_title: '\u0631\u0632\u0631\u0648 \u062A\u0645\u0627\u0633',
        booking_description: '\u06CC\u06A9 \u0632\u0645\u0627\u0646 \u0645\u0646\u0627\u0633\u0628 \u0627\u0646\u062A\u062E\u0627\u0628 \u06A9\u0646\u06CC\u062F \u0648 \u06AF\u0641\u062A\u06AF\u0648 \u06A9\u0646\u06CC\u0645!',
        booking_placeholder: '\u06CC\u06A9 \u062A\u0627\u0631\u06CC\u062E \u0627\u0646\u062A\u062E\u0627\u0628 \u06A9\u0646\u06CC\u062F \u062A\u0627 \u0632\u0645\u0627\u0646\u200C\u0647\u0627\u06CC \u0645\u0648\u062C\u0648\u062F \u0631\u0627 \u0628\u0628\u06CC\u0646\u06CC\u062F',
        cal_sun: '\u06CC\u06A9', cal_mon: '\u062F\u0648', cal_tue: '\u0633\u0647', cal_wed: '\u0686\u0647',
        cal_thu: '\u067E\u0646', cal_fri: '\u062C\u0645', cal_sat: '\u0634\u0646',
        booking_step_date: '\u0627\u0646\u062A\u062E\u0627\u0628 \u062A\u0627\u0631\u06CC\u062E',
        booking_step_time: '\u0627\u0646\u062A\u062E\u0627\u0628 \u0633\u0627\u0639\u062A',
        booking_step_confirm: '\u062A\u0623\u06CC\u06CC\u062F',
        footer_copyright: '&copy; 2025 \u0639\u0644\u06CC\u0631\u0636\u0627 \u062A\u0642\u06CC\u0627\u0646\u06CC \u062E\u0631\u0627\u0633\u06AF\u0627\u0646\u06CC. \u062A\u0645\u0627\u0645 \u062D\u0642\u0648\u0642 \u0645\u062D\u0641\u0648\u0638 \u0627\u0633\u062A.',
        footer_built: '\u0633\u0627\u062E\u062A\u0647 \u0634\u062F\u0647 \u0628\u0627 <i class="fas fa-heart"></i> \u062F\u0631 \u0645\u0648\u0646\u062A\u0631\u0627\u0644',
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

    // Update lang selector to show current language
    const langSelect = document.getElementById('lang-select');
    if (langSelect) langSelect.value = lang;

    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('dir', lang === 'fa' ? 'rtl' : 'ltr');
}

document.getElementById('lang-select')?.addEventListener('change', (e) => {
    localStorage.setItem('lang', e.target.value);
    applyTranslations(e.target.value);
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

// Close mobile menu when clicking a nav link (not dropdown toggles)
document.querySelectorAll('.nav-menu a:not(.nav-dropdown-toggle)').forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
    });
});

// Dropdown toggle (mobile tap / desktop click fallback)
document.querySelectorAll('.nav-dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', (e) => {
        e.preventDefault();
        const dropdown = toggle.closest('.nav-dropdown');
        const isOpen = dropdown.classList.contains('open');
        document.querySelectorAll('.nav-dropdown').forEach(d => d.classList.remove('open'));
        if (!isOpen) dropdown.classList.add('open');
    });
});

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.nav-dropdown')) {
        document.querySelectorAll('.nav-dropdown').forEach(d => d.classList.remove('open'));
    }
});

// Smooth scroll for all anchor links, accounting for fixed navbar
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href === '#') return;
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
            const navbarHeight = document.querySelector('.navbar').offsetHeight;
            window.scrollTo({
                top: target.getBoundingClientRect().top + window.pageYOffset - navbarHeight,
                behavior: 'smooth',
            });
        }
    });
});

// Highlight active nav link/dropdown as sections scroll into view
const pageSections = document.querySelectorAll('section[id]');
if (pageSections.length) {
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const id = entry.target.id;

            // Clear all active states
            document.querySelectorAll('.nav-menu a.active-link').forEach(a => a.classList.remove('active-link'));
            document.querySelectorAll('.nav-dropdown.nav-dropdown-active').forEach(d => d.classList.remove('nav-dropdown-active'));

            // Find nav link with matching data-section
            const activeLink = document.querySelector(`.nav-menu a[data-section="${id}"]`);
            if (activeLink) {
                activeLink.classList.add('active-link');
                const parentDropdown = activeLink.closest('.nav-dropdown');
                if (parentDropdown) parentDropdown.classList.add('nav-dropdown-active');
            }
        });
    }, { rootMargin: '-40% 0px -55% 0px' });

    pageSections.forEach(s => sectionObserver.observe(s));
}

// Navbar is always visible — no hide-on-scroll on the one-pager

// ===== CSS class-based scroll-reveal system =====
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

// Mark grid containers for staggered children
document.querySelectorAll('.projects-grid, .achievement-grid, .volunteer-grid, .skills-grid, .contact-methods').forEach(grid => {
    grid.classList.add('reveal-stagger');
    Array.from(grid.children).forEach((child, i) => {
        child.classList.add('reveal');
        child.style.setProperty('--reveal-i', i);
        revealObserver.observe(child);
    });
});

// Timeline items: alternate slide-in-left / slide-in-right
document.querySelectorAll('.timeline-item').forEach((item, i) => {
    item.classList.add(i % 2 === 0 ? 'reveal-left' : 'reveal-right');
    revealObserver.observe(item);
});

// Section titles: reveal underline
document.querySelectorAll('.section-title').forEach(title => {
    revealObserver.observe(title);
    // The .revealed class triggers the ::after width transition
});

// Booking widget
document.querySelectorAll('.booking-widget').forEach(el => {
    el.classList.add('reveal');
    revealObserver.observe(el);
});

// Skill tags: pop animation when visible
document.querySelectorAll('.skill-tags').forEach(container => {
    const tagObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.querySelectorAll('.skill-tag').forEach((tag, i) => {
                    tag.style.setProperty('--reveal-i', i);
                    tag.classList.add('revealed');
                });
                tagObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });
    tagObserver.observe(container);
});

// Booking Calendar with timezone support (only runs on booking page)
(async function initBooking() {
    // Guard: only initialize if the booking widget is on this page
    if (!document.getElementById('booking-slots')) return;

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
        updateBookingProgress(1);
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

    // Booking progress indicator
    function updateBookingProgress(step) {
        const steps = document.querySelectorAll('.progress-step');
        const lines = document.querySelectorAll('.progress-line');
        steps.forEach((s, i) => {
            const stepNum = i + 1;
            s.classList.remove('active', 'completed');
            if (stepNum < step) s.classList.add('completed');
            else if (stepNum === step) s.classList.add('active');
        });
        lines.forEach((line, i) => {
            if (i + 1 < step) line.classList.add('filled');
            else line.classList.remove('filled');
        });
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
                el.addEventListener('click', (e) => {
                    // Ripple effect
                    const ripple = document.createElement('span');
                    ripple.className = 'ripple';
                    const rect = el.getBoundingClientRect();
                    ripple.style.left = (e.clientX - rect.left - 5) + 'px';
                    ripple.style.top = (e.clientY - rect.top - 5) + 'px';
                    el.appendChild(ripple);
                    ripple.addEventListener('animationend', () => ripple.remove());
                    selectDate(date);
                });
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
        updateBookingProgress(2);
        renderCalendar();
        renderSlots(date);
    }

    function renderSlots(date) {
        const slots = getAvailableSlots(date);
        const dateLabel = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

        if (slots.length === 0) {
            slotsPanel.innerHTML = '<div class="no-slots"><i class="fas fa-moon"></i>No available slots on this day</div>';
            updateBookingProgress(2);
            return;
        }

        let html = `<div class="slots-header">${dateLabel}</div>`;
        for (let i = 0; i < slots.length; i++) {
            html += `<button class="slot-btn" style="--slot-i:${i}" data-idx="${i}"><i class="fas fa-clock"></i> ${slots[i].label}</button>`;
        }
        slotsPanel.innerHTML = html;
        updateBookingProgress(2);

        slotsPanel.querySelectorAll('.slot-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                selectedSlot = slots[+btn.dataset.idx];
                showConfirmForm(dateLabel);
            });
        });
    }

    function showConfirmForm(dateLabel) {
        updateBookingProgress(3);
        slotsPanel.innerHTML = `
            <div class="booking-confirm">
                <button class="back-btn" id="booking-back"><i class="fas fa-arrow-left"></i> Change time</button>
                <div class="selected-slot-summary">
                    <i class="fas fa-clock"></i>
                    <div>
                        <strong>${dateLabel}</strong><br>
                        <span>${selectedSlot.label}</span>
                    </div>
                </div>
                <div class="booking-input-group">
                    <input type="text" id="booking-name" class="booking-input" placeholder=" " required>
                    <label class="booking-label" for="booking-name">Your name</label>
                </div>
                <div class="booking-input-group">
                    <input type="email" id="booking-email" class="booking-input" placeholder=" " required>
                    <label class="booking-label" for="booking-email">Your email</label>
                </div>
                <button class="confirm-btn">Confirm & Send Invite</button>
            </div>`;
        slotsPanel.querySelector('#booking-back').addEventListener('click', () => {
            renderSlots(selectedDate);
        });
        slotsPanel.querySelector('.confirm-btn').addEventListener('click', confirmBooking);
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

