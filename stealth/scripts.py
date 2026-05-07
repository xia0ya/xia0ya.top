"""Stealth scripts for browser fingerprint hiding."""

import random

# Realistic user agents for Chrome, Firefox, Safari, Edge
USER_AGENTS = [
    # Windows Chrome 121
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Windows Chrome 120
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Windows Chrome 122
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Windows Chrome 119
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Mac Chrome 121
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Mac Chrome 120
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Windows Firefox 122
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Windows Firefox 121
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Mac Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Windows Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
]


def get_random_user_agent() -> str:
    """Return a random user agent string."""
    return random.choice(USER_AGENTS)


# Enhanced stealth script - injected into browser context to hide automation fingerprints
ENHANCED_STEALTH_SCRIPT = """
(function() {
    'use strict';

    // Hide webdriver flag
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });

    // Remove CDP detection properties
    delete window.cdc_adoQpoasnfaapdkofahrepdgpnhkgeL;
    delete window.$cdc_asdjflasutopfhvcZLmcfl_;
    delete window.chrome;

    // Mock navigator.plugins with realistic values
    const mockPlugins = [
        {
            name: 'Chrome PDF Plugin',
            description: 'Portable Document Format viewer',
            filename: 'internal-pdf-viewer'
        },
        {
            name: 'Chrome PDF Viewer',
            description: '',
            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'
        },
        {
            name: 'Native Client',
            description: '',
            filename: 'internal-nacl-plugin'
        }
    ];

    Object.defineProperty(navigator, 'plugins', {
        get: () => mockPlugins,
        configurable: true
    });

    // Mock navigator.languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'zh-CN', 'zh'],
        configurable: true
    });

    // Handle permissions.query - mock common permissions
    const originalQuery = navigator.permissions.query;
    if (originalQuery) {
        navigator.permissions.query = function(query) {
            const permissionToMock = ['geolocation', 'notifications', 'push', 'midi'];
            if (permissionToMock.includes(query.name)) {
                return Promise.resolve({ state: 'prompt', onchange: null });
            }
            return originalQuery.call(this, query);
        };
    }

    // WebGL fingerprint randomization
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };

    // Prevent iframe detection
    Object.defineProperty(window, 'top', {
        get: function() { return window; }
    });

    // Remove automation-related properties
    delete window.callPhantom;
    delete window._phantom;
    delete window.puppeteer;
    delete window.playwright;
    delete window.__playwright_unlocked;

    // Prevent detection via document attributes
    if (document.documentElement) {
        delete document.documentElement.style['-webkit-appearance'];
    }

    // Block automation detection in console
    const consoleType = console.toString();
    if (consoleType.includes('native code') === false) {
        console.toString = function() {
            return 'function log() { [native code] }';
        };
    }
})();
"""


def get_stealth_script() -> str:
    """Return the enhanced stealth JavaScript script."""
    return ENHANCED_STEALTH_SCRIPT
