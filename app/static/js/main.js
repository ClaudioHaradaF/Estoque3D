(function() {
    'use strict';

    // ===== SCROLL PROGRESS BAR =====
    var progressBar = document.getElementById('scrollProgress');
    if (progressBar) {
        window.addEventListener('scroll', function() {
            var scrollTop = window.scrollY;
            var docHeight = document.documentElement.scrollHeight - window.innerHeight;
            progressBar.style.width = (docHeight > 0 ? (scrollTop / docHeight) * 100 : 0) + '%';
        }, { passive: true });
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
        var metaTheme = document.querySelector('meta[name="theme-color"]');
        if (metaTheme) {
            metaTheme.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#f5f0eb');
        }
        if (typeof Chart !== 'undefined') {
            if (theme === 'dark') {
                Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(30,30,30,0.98)';
                Chart.defaults.plugins.tooltip.titleColor = '#e8e8e8';
                Chart.defaults.plugins.tooltip.bodyColor = '#a8a8a8';
                Chart.defaults.plugins.tooltip.borderColor = '#444';
            } else {
                Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(245,240,235,0.98)';
                Chart.defaults.plugins.tooltip.titleColor = '#2c2c2c';
                Chart.defaults.plugins.tooltip.bodyColor = '#5c5550';
                Chart.defaults.plugins.tooltip.borderColor = '#e8e0d8';
            }
        }
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

    // ===== CURSOR FOLLOWER (desktop only) =====
    if (!window.matchMedia || !window.matchMedia('(pointer: coarse)').matches) {
        var cursorDot = document.createElement('div');
        cursorDot.className = 'cursor-dot';
        document.body.appendChild(cursorDot);

        var mouseX = -100, mouseY = -100, dotX = -100, dotY = -100;
        document.addEventListener('mousemove', function(e) {
            mouseX = e.clientX;
            mouseY = e.clientY;
        }, { passive: true });

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
    }

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

    // ===== COLOR THEME ENGINE =====
    function setAccentColor(color) {
        document.documentElement.setAttribute('data-accent', color);
        localStorage.setItem('accentColor', color);
        document.querySelectorAll('.theme-swatches .swatch').forEach(function(s) {
            s.classList.toggle('active', s.getAttribute('data-color') === color);
        });
        // Update Chart.js tooltip border to match accent
        if (typeof Chart !== 'undefined') {
            var accentMap = { vermelhão: '#BC002D', indigo: '#2c3e6b', dourado: '#b8860b', verde: '#2d7d5a' };
            Chart.defaults.plugins.tooltip.borderColor = accentMap[color] || '#BC002D';
        }
    }

    var savedAccent = localStorage.getItem('accentColor') || 'vermelhão';
    setAccentColor(savedAccent);

    document.addEventListener('click', function(e) {
        var swatch = e.target.closest('.theme-swatches .swatch');
        if (swatch) setAccentColor(swatch.getAttribute('data-color'));
    });

    // ===== ANIMATED TYPOGRAPHY (title reveal) =====
    document.querySelectorAll('.text-reveal').forEach(function(el) {
        var text = el.textContent.trim();
        el.innerHTML = '';
        for (var i = 0; i < text.length; i++) {
            var span = document.createElement('span');
            span.className = 'reveal-inner';
            span.textContent = text[i] === ' ' ? '\u00a0' : text[i];
            el.appendChild(span);
        }
    });

    // ===== LOADING SCREEN =====
    var loadingScreen = document.querySelector('.loading-screen');
    if (loadingScreen) {
        function hideLoading() {
            loadingScreen.classList.add('loaded');
            setTimeout(function() { loadingScreen.style.display = 'none'; }, 700);
        }
        if (document.readyState === 'complete') {
            setTimeout(hideLoading, 300);
        } else {
            window.addEventListener('load', function() { setTimeout(hideLoading, 400); });
            // Fallback: hide after 3s even if something is slow
            setTimeout(hideLoading, 3000);
        }
    }

    // ===== COMMAND PALETTE (Ctrl+K / Cmd+K) =====
    (function() {
        var overlay = document.getElementById('cmdPalette');
        var input = document.getElementById('cmdInput');
        var results = document.getElementById('cmdResults');
        if (!overlay || !input || !results) return;

        var timer;
        var items = [];
        var highlightIdx = -1;

        function openPalette() {
            overlay.classList.add('open');
            setTimeout(function() { input.focus(); }, 100);
            highlightIdx = -1;
            if (input.value.length >= 2) buscar(input.value);
        }

        function closePalette() {
            overlay.classList.remove('open');
            input.blur();
            highlightIdx = -1;
        }

        function buscar(q) {
            clearTimeout(timer);
            q = q.trim().toLowerCase();
            if (q.length < 2) {
                results.innerHTML = '<div class="cmd-empty">Digite pelo menos 2 caracteres para buscar</div>';
                items = [];
                return;
            }
            timer = setTimeout(function() {
                fetch('/api/search?q=' + encodeURIComponent(q))
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        items = data;
                        renderResults(data);
                    });
            }, 200);
        }

        function renderResults(data) {
            if (data.length === 0) {
                results.innerHTML = '<div class="cmd-empty">Nenhum resultado encontrado</div>';
                return;
            }
            var groups = {};
            data.forEach(function(item) {
                if (!groups[item.typeLabel]) groups[item.typeLabel] = [];
                groups[item.typeLabel].push(item);
            });
            var html = '';
            var order = ['Produto', 'Venda', 'Insumo', 'Categoria'];
            order.forEach(function(label) {
                var arr = groups[label];
                if (!arr) return;
                html += '<div class="cmd-group">' + label + '</div>';
                arr.forEach(function(item) {
                    html += '<a class="cmd-item" href="' + item.url + '">' +
                        '<div class="cmd-icon"><i class="bi bi-' + item.icon + '"></i></div>' +
                        '<div class="cmd-text">' +
                            '<div class="cmd-label">' + item.label + '</div>' +
                            '<div class="cmd-sub">' + (item.sub || '') + '</div>' +
                        '</div>' +
                        '<span class="cmd-badge">' + (item.type === 'produto' ? 'Produto' : item.type === 'venda' ? 'Venda' : '') + '</span>' +
                    '</a>';
                });
            });
            results.innerHTML = html;
            results.querySelectorAll('.cmd-item').forEach(function(el, i) {
                el.addEventListener('click', function(e) {
                    e.preventDefault();
                    closePalette();
                    window.location.href = el.getAttribute('href');
                });
            });
            highlightIdx = -1;
        }

        function navigate(delta) {
            var anchors = results.querySelectorAll('.cmd-item');
            if (anchors.length === 0) return;
            if (highlightIdx >= 0) anchors[highlightIdx].classList.remove('highlighted');
            highlightIdx += delta;
            if (highlightIdx < 0) highlightIdx = anchors.length - 1;
            if (highlightIdx >= anchors.length) highlightIdx = 0;
            anchors[highlightIdx].classList.add('highlighted');
            anchors[highlightIdx].scrollIntoView({ block: 'nearest' });
        }

        // Keyboard: Ctrl+K / Cmd+K to open
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                if (overlay.classList.contains('open')) closePalette();
                else openPalette();
            }
            if (e.key === 'Escape' && overlay.classList.contains('open')) {
                closePalette();
            }
        });

        input.addEventListener('input', function() {
            buscar(input.value);
        });

        input.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowDown') { e.preventDefault(); navigate(1); }
            if (e.key === 'ArrowUp') { e.preventDefault(); navigate(-1); }
            if (e.key === 'Enter') {
                e.preventDefault();
                var anchors = results.querySelectorAll('.cmd-item');
                if (highlightIdx >= 0 && anchors[highlightIdx]) {
                    closePalette();
                    window.location.href = anchors[highlightIdx].getAttribute('href');
                } else if (anchors.length > 0) {
                    closePalette();
                    window.location.href = anchors[0].getAttribute('href');
                }
            }
        });

        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) closePalette();
        });

        // Close on blur if clicked outside
        input.addEventListener('blur', function() {
            setTimeout(function() {
                if (!overlay.contains(document.activeElement)) closePalette();
            }, 200);
        });
    })();

    // ===== KPI SPARKLINES =====
    document.querySelectorAll('.kpi-sparkline[data-values]').forEach(function(el) {
        var values = el.getAttribute('data-values').split(',').map(Number);
        if (values.length < 2) return;
        var w = 80, h = 28;
        var max = Math.max.apply(null, values);
        var min = Math.min.apply(null, values);
        var range = max - min || 1;
        var pad = 2;
        var points = values.map(function(v, i) {
            var x = pad + (i / (values.length - 1)) * (w - pad * 2);
            var y = h - pad - ((v - min) / range) * (h - pad * 2);
            return x + ',' + y;
        });
        var d = 'M' + points.join(' L');
        el.innerHTML = '<svg viewBox="0 0 ' + w + ' ' + h + '" xmlns="http://www.w3.org/2000/svg"><path d="' + d + '"/></svg>';
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
    var theme = document.documentElement.getAttribute('data-theme') || 'light';
    if (theme === 'dark') {
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(30,30,30,0.98)';
        Chart.defaults.plugins.tooltip.titleColor = '#e8e8e8';
        Chart.defaults.plugins.tooltip.bodyColor = '#a8a8a8';
        Chart.defaults.plugins.tooltip.borderColor = '#444';
    } else {
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(245,240,235,0.98)';
        Chart.defaults.plugins.tooltip.titleColor = '#2c2c2c';
        Chart.defaults.plugins.tooltip.bodyColor = '#5c5550';
        Chart.defaults.plugins.tooltip.borderColor = '#e8e0d8';
    }
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
})();

// ===== DIRTY FORM WARNING =====
(function() {
    var forms = document.querySelectorAll('form:not(.date-filter):not(.search-box)');
    forms.forEach(function(form) {
        var dirty = false;
        var inputs = form.querySelectorAll('input:not([type="hidden"]):not([type="file"]), select, textarea');
        inputs.forEach(function(input) {
            var origValue = input.value;
            input.addEventListener('change', function() { dirty = true; });
            input.addEventListener('input', function() {
                if (input.value !== origValue) dirty = true;
            });
        });
        form.addEventListener('submit', function() { dirty = false; });
        window.addEventListener('beforeunload', function(e) {
            if (dirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    });
})();

// ===== BADGE API (PWA app badge) =====
(function() {
    if (!navigator.setAppBadge && !navigator.setExperimentalAppBadge) return;

    function updateBadge(count) {
        count = count || 0;
        var sw = navigator.serviceWorker;
        if (sw && sw.controller) {
            sw.controller.postMessage({ type: count > 0 ? 'SET_BADGE' : 'CLEAR_BADGE', count: count });
        }
    }

    // Check for low stock count
    var baixoEstoqueEl = document.querySelector('[data-baixo-estoque-count]');
    if (baixoEstoqueEl) {
        var count = parseInt(baixoEstoqueEl.getAttribute('data-baixo-estoque-count')) || 0;
        updateBadge(count);
    }

    // Listen for badge updates from server pushes
    navigator.serviceWorker.addEventListener('message', function(e) {
        if (e.data && e.data.type === 'BADGE_UPDATE') {
            updateBadge(e.data.count);
        }
    });
})();