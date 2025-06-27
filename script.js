// Enhanced animation and interaction functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling for any anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add button click handlers
    const primaryBtn = document.querySelector('.btn-primary');
    const secondaryBtn = document.querySelector('.btn-secondary');
    const githubBtn = document.querySelector('.btn-github');

    if (primaryBtn) {
        primaryBtn.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Here you would typically redirect to download or handle the action
            console.log('Download Personal Edition clicked');
        });
    }

    if (secondaryBtn) {
        secondaryBtn.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Here you would typically show enterprise info or handle the action
            console.log('Explore Enterprise Solution clicked');
        });
    }

    if (githubBtn) {
        githubBtn.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Here you would typically redirect to GitHub repository
            console.log('View on GitHub clicked');
            // window.open('https://github.com/your-repo', '_blank');
        });
    }

    // Handle multiple buttons with same classes
    const allPrimaryBtns = document.querySelectorAll('.btn-primary');
    const allSecondaryBtns = document.querySelectorAll('.btn-secondary');

    allPrimaryBtns.forEach((btn, index) => {
        btn.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Different actions based on button text
            const buttonText = this.textContent.trim();
            switch(buttonText) {
                case 'Download Personal Edition':
                    console.log('Download Personal Edition clicked');
                    // window.open('download-link', '_blank');
                    break;
                default:
                    console.log('Primary button clicked:', buttonText);
            }
        });
    });

    allSecondaryBtns.forEach((btn, index) => {
        btn.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Different actions based on button text
            const buttonText = this.textContent.trim();
            switch(buttonText) {
                case 'Explore Enterprise Solution':
                    console.log('Explore Enterprise Solution clicked');
                    // Scroll to enterprise section or show modal
                    break;
                case 'Talk to Sales':
                    console.log('Talk to Sales clicked');
                    // window.open('mailto:sales@echoprompt.com', '_blank');
                    break;
                case 'See Demo':
                    console.log('See Demo clicked');
                    // Show demo modal or redirect
                    break;
                default:
                    console.log('Secondary button clicked:', buttonText);
            }
        });
    });

    // Feature cards interaction
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        // Add staggered animation delay
        card.style.animationDelay = `${1.2 + (index * 0.1)}s`;
        
        // Add click handler
        card.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'scale(1.02)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
            
            // Here you would typically navigate to feature details or show more info
            console.log('Feature card clicked:', this.querySelector('.feature-title').textContent);
        });

        // Add keyboard navigation
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });

    // Footer links interaction
    const footerLinks = document.querySelectorAll('.footer-link');
    footerLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Here you would typically navigate to the respective pages
            console.log('Footer link clicked:', this.textContent);
            
            // Example navigation logic
            const linkText = this.textContent.toLowerCase();
            switch(linkText) {
                case 'product':
                    // Navigate to product page
                    console.log('Navigating to Product page');
                    break;
                case 'docs':
                    // Navigate to documentation
                    console.log('Navigating to Documentation');
                    break;
                case 'github':
                    // Navigate to GitHub
                    console.log('Navigating to GitHub');
                    // window.open('https://github.com/your-repo', '_blank');
                    break;
                case 'contact':
                    // Navigate to contact page
                    console.log('Navigating to Contact page');
                    break;
            }
        });
    });

    // Social media links interaction
    const socialLinks = document.querySelectorAll('.social-link');
    socialLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add click animation
            this.style.transform = 'scale(0.9)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Here you would typically redirect to social media profiles
            const ariaLabel = this.getAttribute('aria-label');
            console.log('Social link clicked:', ariaLabel);
            
            // Example social media navigation logic
            switch(ariaLabel) {
                case 'Twitter':
                    // window.open('https://twitter.com/your-handle', '_blank');
                    console.log('Opening Twitter profile');
                    break;
                case 'GitHub':
                    // window.open('https://github.com/your-repo', '_blank');
                    console.log('Opening GitHub profile');
                    break;
                case 'LinkedIn':
                    // window.open('https://linkedin.com/company/your-company', '_blank');
                    console.log('Opening LinkedIn profile');
                    break;
                case 'Discord':
                    // window.open('https://discord.gg/your-server', '_blank');
                    console.log('Opening Discord server');
                    break;
            }
        });
    });

    // Add intersection observer for additional animations
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

    // Observe hero elements for additional animation triggers
    const heroElements = document.querySelectorAll('.hero-headline, .hero-subheadline, .hero-buttons');
    heroElements.forEach(el => observer.observe(el));

    // Observe feature cards for scroll-triggered animations
    const featureElements = document.querySelectorAll('.feature-card');
    featureElements.forEach(el => observer.observe(el));

    // Observe open source section for scroll-triggered animations
    const opensourceElements = document.querySelectorAll('.opensource-content');
    opensourceElements.forEach(el => observer.observe(el));

    // Observe new sections for scroll-triggered animations
    const sectionElements = document.querySelectorAll('.section-content, .enterprise-feature');
    sectionElements.forEach(el => observer.observe(el));

    // Observe footer for scroll-triggered animations
    const footerElements = document.querySelectorAll('.footer');
    footerElements.forEach(el => observer.observe(el));

    // Add parallax effect to background (subtle)
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero');
        if (hero) {
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        }
    });

    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            const focusedElement = document.activeElement;
            if (focusedElement && (focusedElement.classList.contains('btn') || 
                                  focusedElement.classList.contains('footer-link') || 
                                  focusedElement.classList.contains('social-link'))) {
                e.preventDefault();
                focusedElement.click();
            }
        }
    });

    // Add smooth scroll behavior for better UX
    document.documentElement.style.scrollBehavior = 'smooth';
}); 