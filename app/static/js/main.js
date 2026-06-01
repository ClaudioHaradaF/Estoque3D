(function() {
    'use strict';

    // ===== SCROLL PROGRESS BAR =====
    var progressBar = document.getElementById('scrollProgress');
    if (progressBar) {
        window.addEventListener('scroll', function() {
            var scrollTop = window.scrollY;
            var docHeight = document.documentElement.scrollHeight - window.innerHeight;
            progressBar.style.width = (docHeight > 0 ? (scrollTop / docHeight) * 100 : 0) + '%';
        });
    }

    // ===== RIPPLE EFFECT =====
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('.btn');
        if (!btn) return;
        var rect = btn.getBoundingClientRect();
        var size = Math.max(rect.width, rect.height);
        var ripple = document.createElement('span');
        ripple.style.cssText = 'position:absolute;top:' + (e.clientY - rect.top - size / 2) + 'px;left:' + (e.clientX - rect.left - size / 2) + 'px;width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:rgba(188,0,45,0.2);transform:scale(0);animation:rippleAnim 0.5s ease-out;pointer-events:none;z-index:0';
        btn.style.position = 'relative';
        btn.style.overflow = 'hidden';
        btn.appendChild(ripple);
        setTimeout(function() { ripple.remove(); }, 600);
    });

    if (!document.getElementById('rippleStyle')) {
        var s = document.createElement('style');
        s.id = 'rippleStyle';
        s.textContent = '@keyframes rippleAnim { to { transform: scale(2.5); opacity: 0; } }';
        document.head.appendChild(s);
    }

    // ===== INTERSECTION OBSERVER =====
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
    document.querySelectorAll('.animate-on-scroll').forEach(function(el) { observer.observe(el); });

    // ===== KPI COUNTER =====
    function easeOutExpo(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); }
    function animateValue(el, start, end, duration, suffix) {
        if (!el) return;
        var startTime = null;
        suffix = suffix || '';
        function step(ts) {
            if (!startTime) startTime = ts;
            var p = Math.min((ts - startTime) / duration, 1);
            var cur = Math.round(start + (end - start) * easeOutExpo(p));
            el.textContent = cur.toLocaleString('pt-BR') + suffix;
            if (p < 1) requestAnimationFrame(step);
            else el.textContent = end.toLocaleString('pt-BR') + suffix;
        }
        requestAnimationFrame(step);
    }
    function animateMoney(el, end, duration) {
        if (!el) return;
        var startTime = null;
        function step(ts) {
            if (!startTime) startTime = ts;
            var p = Math.min((ts - startTime) / duration, 1);
            var cur = start + (end - start) * easeOutExpo(p);
            el.textContent = 'R$ ' + cur.toFixed(2).replace('.', ',');
            if (p < 1) requestAnimationFrame(step);
            else el.textContent = 'R$ ' + end.toFixed(2).replace('.', ',');
        }
        requestAnimationFrame(step);
    }
    document.querySelectorAll('.kpi-value[data-count]').forEach(function(el) {
        var target = parseFloat(el.getAttribute('data-count'));
        if (el.getAttribute('data-money') === 'true') animateMoney(el, target, 1500);
        else animateValue(el, 0, target, 1400);
    });

    // ===== DARK MODE =====
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        var btn = document.querySelector('.theme-toggle');
        if (btn) btn.innerHTML = theme === 'dark' ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon"></i>';
    }

    var savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTheme('dark');
    }

    document.addEventListener('click', function(e) {
        var btn = e.target.closest('.theme-toggle');
        if (!btn) return;
        var current = document.documentElement.getAttribute('data-theme');
        setTheme(current === 'dark' ? 'light' : 'dark');
    });

    // ===== TOAST SYSTEM =====
    var toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    window.showToast = function(message, type) {
        type = type || 'info';
        var icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.innerHTML = '<div class="toast-content"><i class="bi ' + (icons[type] || icons.info) + ' toast-icon"></i>' + message + '</div><div class="toast-bar"></div>';
        toastContainer.appendChild(toast);
        setTimeout(function() {
            toast.classList.add('toast-out');
            setTimeout(function() { toast.remove(); }, 300);
        }, 4000);
    };

    // Convert flash messages to toasts
    document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
        var msg = alert.childNodes[0].textContent.trim();
        var cls = 'info';
        if (alert.classList.contains('alert-success')) cls = 'success';
        else if (alert.classList.contains('alert-danger')) cls = 'error';
        else if (alert.classList.contains('alert-warning')) cls = 'warning';
        if (msg) window.showToast(msg, cls);
        alert.remove();
    });

    // ===== MODAL SYSTEM =====
    var modalOverlay = document.querySelector('.modal-overlay');
    if (!modalOverlay) {
        modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';
        modalOverlay.innerHTML = '<div class="modal-content"><div class="modal-icon"></div><h3></h3><p></p><div class="modal-actions"></div></div>';
        document.body.appendChild(modalOverlay);
    }

    modalOverlay.addEventListener('click', function(e) {
        if (e.target === modalOverlay) closeModal();
    });

    window.showModal = function(iconHtml, title, message, confirmText, cancelText, onConfirm) {
        modalOverlay.querySelector('.modal-icon').innerHTML = iconHtml || '';
        modalOverlay.querySelector('h3').textContent = title || '';
        modalOverlay.querySelector('p').textContent = message || '';
        var actions = modalOverlay.querySelector('.modal-actions');
        actions.innerHTML = '';
        if (cancelText !== false) {
            var cancelBtn = document.createElement('button');
            cancelBtn.className = 'btn btn-outline-secondary';
            cancelBtn.textContent = cancelText || 'Cancelar';
            cancelBtn.addEventListener('click', closeModal);
            actions.appendChild(cancelBtn);
        }
        if (confirmText) {
            var confirmBtn = document.createElement('button');
            confirmBtn.className = 'btn btn-primary';
            confirmBtn.textContent = confirmText;
            confirmBtn.addEventListener('click', function() {
                if (onConfirm) onConfirm();
                closeModal();
            });
            actions.appendChild(confirmBtn);
        }
        modalOverlay.classList.add('active');
    };

    function closeModal() {
        modalOverlay.classList.remove('active');
    }

    // Replace confirm dialogs with modal (onclick and onsubmit)
    function replaceConfirm(el, attr) {
        var code = el.getAttribute(attr);
        if (!code || !code.includes('confirm(')) return;
        el.removeAttribute(attr);
        el.addEventListener(attr === 'onsubmit' ? 'submit' : 'click', function(e) {
            e.preventDefault();
            var match = code.match(/confirm\(['"](.+?)['"]\)/);
            var msg = match ? match[1] : 'Tem certeza?';
            var href = el.getAttribute('href') || '';
            showModal('<i class="bi bi-exclamation-triangle-fill" style="color:var(--accent);"></i>', 'Confirmar', msg, 'Confirmar', 'Cancelar', function() {
                if (href) window.location.href = href;
                else if (el.tagName === 'FORM') el.submit();
            });
        });
    }
    document.querySelectorAll('[onclick*="confirm"]').forEach(function(el) { replaceConfirm(el, 'onclick'); });
    document.querySelectorAll('[onsubmit*="confirm"]').forEach(function(el) { replaceConfirm(el, 'onsubmit'); });

    // ===== CURSOR FOLLOWER =====
    var cursorDot = document.createElement('div');
    cursorDot.className = 'cursor-dot';
    document.body.appendChild(cursorDot);

    var mouseX = -100, mouseY = -100, dotX = -100, dotY = -100;
    document.addEventListener('mousemove', function(e) {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animateCursor() {
        dotX += (mouseX - dotX) * 0.15;
        dotY += (mouseY - dotY) * 0.15;
        cursorDot.style.left = dotX + 'px';
        cursorDot.style.top = dotY + 'px';
        requestAnimationFrame(animateCursor);
    }
    animateCursor();

    document.querySelectorAll('.btn, .glass-card, a, .kpi-card').forEach(function(el) {
        el.addEventListener('mouseenter', function() { cursorDot.classList.add('hovering'); });
        el.addEventListener('mouseleave', function() { cursorDot.classList.remove('hovering'); });
    });

    // ===== MAGNETIC BUTTONS =====
    document.querySelectorAll('.btn').forEach(function(btn) {
        btn.addEventListener('mousemove', function(e) {
            var rect = this.getBoundingClientRect();
            var x = e.clientX - rect.left - rect.width / 2;
            var y = e.clientY - rect.top - rect.height / 2;
            var strength = Math.min(Math.abs(x), Math.abs(y)) * 0.08;
            this.style.transform = 'translate(' + (x * 0.12) + 'px, ' + (y * 0.12) + 'px)';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translate(0, 0)';
        });
    });

    // ===== 3D TILT CARDS =====
    document.querySelectorAll('.glass-card').forEach(function(card) {
        card.addEventListener('mousemove', function(e) {
            var rect = this.getBoundingClientRect();
            var x = (e.clientX - rect.left) / rect.width - 0.5;
            var y = (e.clientY - rect.top) / rect.height - 0.5;
            this.style.transform = 'perspective(800px) rotateY(' + (x * 4) + 'deg) rotateX(' + (-y * 4) + 'deg) translateY(-2px)';
            this.style.boxShadow = '0 8px 32px rgba(0,0,0,0.08)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(800px) rotateY(0deg) rotateX(0deg) translateY(0px)';
            this.style.boxShadow = '';
        });
    });

    // ===== HAMBURGER MOBILE =====
    var hamburger = document.querySelector('.hamburger');
    var navLinks = document.querySelector('.nav-links');
    var navOverlay = document.querySelector('.nav-overlay');
    if (hamburger && navLinks) {
        function closeMenu() {
            navLinks.classList.remove('open');
            if (navOverlay) navOverlay.classList.remove('active');
            hamburger.innerHTML = '<i class="bi bi-list"></i>';
        }
        hamburger.addEventListener('click', function() {
            var isOpen = navLinks.classList.toggle('open');
            if (navOverlay) navOverlay.classList.toggle('active', isOpen);
            this.innerHTML = isOpen ? '<i class="bi bi-x-lg"></i>' : '<i class="bi bi-list"></i>';
        });
        if (navOverlay) {
            navOverlay.addEventListener('click', closeMenu);
        }
        navLinks.querySelectorAll('a').forEach(function(a) {
            a.addEventListener('click', closeMenu);
        });
    }

    // ===== PAGE TRANSITIONS =====
    var transitionOverlay = document.createElement('div');
    transitionOverlay.className = 'page-transition-overlay';
    document.body.prepend(transitionOverlay);

    document.querySelectorAll('a:not([target="_blank"])').forEach(function(link) {
        var href = link.getAttribute('href');
        if (href && href.startsWith('/') && !href.startsWith('//')) {
            link.addEventListener('click', function(e) {
                // View Transitions API progressive enhancement
                if (document.startViewTransition) {
                    e.preventDefault();
                    var dest = href;
                    document.startViewTransition(function() {
                        window.location.href = dest;
                    });
                } else {
                    transitionOverlay.classList.add('active');
                    setTimeout(function() { transitionOverlay.classList.remove('active'); }, 400);
                }
            });
        }
    });

    window.addEventListener('pageshow', function() {
        transitionOverlay.classList.remove('active');
        var main = document.querySelector('.page-body');
        if (main) {
            main.style.opacity = '1';
            main.style.transform = 'translateY(0)';
        }
    });

    // ===== NAVBAR ACTIVE INDICATOR =====
    var activeLink = document.querySelector('.nav-links a.active');
    if (activeLink) activeLink.style.transition = 'color 0.3s ease';

    // ===== LINK UNDERLINE =====
    document.querySelectorAll('a:not(.nav-links a):not(.btn)').forEach(function(link) {
        if (link.getAttribute('href') && !link.getAttribute('href').startsWith('#')) {
            link.classList.add('content-link');
        }
    });

    // ===== LAZY IMAGE HANDLER =====
    document.querySelectorAll('img[loading="lazy"]').forEach(function(img) {
        if (img.complete) img.classList.add('loaded');
        else img.addEventListener('load', function() { this.classList.add('loaded'); });
    });

})();

// ===== CHART.JS PLUGIN: PROGRESSIVE LINE =====
(function() {
    if (typeof Chart === 'undefined') return;
    var progressiveLinePlugin = {
        id: 'progressiveLine',
        beforeDraw: function(chart) {
            if (chart.config.type !== 'line') return;
            var meta = chart.getDatasetMeta(0);
            if (!meta || !meta.data || meta.data.length === 0) return;
            if (chart._progressiveDone) return;
            var width = chart.chartArea.right - chart.chartArea.left;
            var progress = Math.min((Date.now() - chart._progressiveStart) / 1800, 1);
            if (progress >= 1) { chart._progressiveDone = true; return; }
            var eased = 1 - Math.pow(1 - progress, 3);
            var clipWidth = width * eased;
            var startX = chart.chartArea.left;
            var ctx = chart.ctx;
            ctx.save();
            ctx.beginPath();
            ctx.rect(startX, chart.chartArea.top, clipWidth, chart.chartArea.bottom - chart.chartArea.top);
            ctx.clip();
            chart.draw();
            ctx.restore();
            chart.draw();
            requestAnimationFrame(function() { chart.draw(); });
        }
    };
    Chart.register(progressiveLinePlugin);
    var orig = Chart.prototype.construct;
    if (orig) {
        Chart.prototype.construct = function() {
            orig.apply(this, arguments);
            this._progressiveStart = Date.now();
        };
    }
})();

// ===== CHART.JS TOOLTIP DEFAULTS =====
(function() {
    if (typeof Chart === 'undefined') return;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(245,240,235,0.98)';
    Chart.defaults.plugins.tooltip.titleColor = '#2c2c2c';
    Chart.defaults.plugins.tooltip.bodyColor = '#5c5550';
    Chart.defaults.plugins.tooltip.borderColor = '#e8e0d8';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
})();