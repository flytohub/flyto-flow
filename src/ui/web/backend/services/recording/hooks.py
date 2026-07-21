"""
Recording Hooks

Playwright hooks for recording browser interactions.
"""

# JavaScript injection script for recording
RECORDING_SCRIPT = """
window.__flytoRecorder = {
    cssString: function(value) {
        return String(value)
            .replace(/\\/g, '\\\\')
            .replace(/"/g, '\\"')
            .replace(/\n/g, '\\A ');
    },
    cssIdentifier: function(value) {
        if (window.CSS && typeof window.CSS.escape === 'function') {
            return window.CSS.escape(String(value));
        }
        return String(value).replace(/([^a-zA-Z0-9_-])/g, '\\$1');
    },
    attrSelector: function(name, value) {
        return `[${name}="${this.cssString(value)}"]`;
    },
    textSelector: function(tagName, text) {
        return `${tagName.toLowerCase()}:has-text("${this.cssString(text)}")`;
    },
    getSelector: function(element) {
        // Try data-testid first
        if (element.dataset && element.dataset.testid) {
            return this.attrSelector('data-testid', element.dataset.testid);
        }
        // Try data-cy (Cypress)
        if (element.dataset && element.dataset.cy) {
            return this.attrSelector('data-cy', element.dataset.cy);
        }
        // Try ID
        if (element.id) {
            return `#${this.cssIdentifier(element.id)}`;
        }
        // Try role + accessible name
        if (element.getAttribute('role')) {
            const role = element.getAttribute('role');
            const ariaLabel = element.getAttribute('aria-label');
            const textName = element.innerText?.trim()?.substring(0, 30);
            if (ariaLabel) {
                return `[role="${this.cssString(role)}"][aria-label="${this.cssString(ariaLabel)}"]`;
            }
            if (textName) {
                return `[role="${this.cssString(role)}"]:has-text("${this.cssString(textName)}")`;
            }
        }
        // Try text content for buttons/links
        if (['BUTTON', 'A', 'LABEL'].includes(element.tagName)) {
            const text = element.innerText?.trim();
            if (text && text.length < 50) {
                return this.textSelector(element.tagName, text);
            }
        }
        // Fallback to CSS path
        return this.getCssPath(element);
    },
    getCssPath: function(element) {
        const path = [];
        while (element && element !== document.body) {
            let selector = element.tagName.toLowerCase();
            if (element.id) {
                selector = `#${this.cssIdentifier(element.id)}`;
                path.unshift(selector);
                break;
            }
            const siblings = Array.from(element.parentElement?.children || [])
                .filter(el => el.tagName === element.tagName);
            if (siblings.length > 1) {
                const index = siblings.indexOf(element) + 1;
                selector += `:nth-of-type(${index})`;
            }
            path.unshift(selector);
            element = element.parentElement;
        }
        return path.join(' > ');
    },
    getAlternatives: function(element) {
        const alts = [];
        // data-testid
        if (element.dataset?.testid) {
            alts.push({type: 'data-testid', selector: this.attrSelector('data-testid', element.dataset.testid), score: 95});
        }
        // ID
        if (element.id) {
            alts.push({type: 'id', selector: `#${this.cssIdentifier(element.id)}`, score: 90});
        }
        // text
        if (['BUTTON', 'A'].includes(element.tagName)) {
            const text = element.innerText?.trim();
            if (text && text.length < 50) {
                alts.push({type: 'text', selector: this.textSelector(element.tagName, text), score: 80});
            }
        }
        // CSS
        alts.push({type: 'css', selector: this.getCssPath(element), score: 50});
        return alts;
    }
};

// Override click
document.addEventListener('click', function(e) {
    const selector = window.__flytoRecorder.getSelector(e.target);
    const alternatives = window.__flytoRecorder.getAlternatives(e.target);
    window.__flytoLastAction = {
        type: 'click',
        selector: selector,
        alternatives: alternatives,
        tagName: e.target.tagName,
        text: e.target.innerText?.substring(0, 100)
    };
}, true);

// Override input
document.addEventListener('input', function(e) {
    if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
        const selector = window.__flytoRecorder.getSelector(e.target);
        window.__flytoLastAction = {
            type: 'fill',
            selector: selector,
            value: e.target.value,
            inputType: e.target.type
        };
    }
}, true);

// Override change (for selects)
document.addEventListener('change', function(e) {
    if (e.target.tagName === 'SELECT') {
        const selector = window.__flytoRecorder.getSelector(e.target);
        window.__flytoLastAction = {
            type: 'select',
            selector: selector,
            value: e.target.value
        };
    } else if (e.target.type === 'checkbox' || e.target.type === 'radio') {
        const selector = window.__flytoRecorder.getSelector(e.target);
        window.__flytoLastAction = {
            type: e.target.checked ? 'check' : 'uncheck',
            selector: selector
        };
    }
}, true);
"""
