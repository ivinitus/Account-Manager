
// ==UserScript==
// @name         Account Manager
// @namespace    http://tampermonkey.net/
// @version      4.3
// @description  Enhanced UI with last used account fetcher and active login using same logic as other buttons
// @author       Vinitus
// @include      https://pre-prod.amazon.*/*
// @include      https://es-pre-prod.amazon.*/*
// @include      https://www.amazon.*/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const waitFor = (sel, t = 12000) => new Promise((ok, bad) => {
        const st = Date.now();
        const iv = setInterval(() => {
            const el = document.querySelector(sel);
            if (el) { clearInterval(iv); ok(el); }
            else if (Date.now() - st > t) { clearInterval(iv); bad(`timeout: ${sel}`); }
        }, 250);
    });

    const host2Mkt = h => {
    const m = {
        'amazon.co.uk': 'uk', 'audible.co.uk': 'uk',
        'amazon.in': 'in', 'audible.in': 'in',
        'amazon.com.br': 'br', 'audible.com.br': 'br',
        'amazon.ca': 'ca', 'audible.ca': 'ca',
        'amazon.com.au': 'au', 'audible.com.au': 'au',
        'amazon.co.jp': 'jp', 'audible.co.jp': 'jp',
        'amazon.de': 'de', 'audible.de': 'de',
        'amazon.fr': 'fr', 'audible.fr': 'fr',
        'amazon.it': 'it', 'audible.it': 'it',
        'amazon.es': 'es', 'audible.es': 'es',
        'amazon.com': 'us', 'audible.com': 'us'
    };

    const prefixMatch = h.match(/^([a-z]{2})[-\.]/);
    if (prefixMatch && m[`amazon.${prefixMatch[1]}`]) {
        return prefixMatch[1];
    }

    const domainMatch = h.match(/(amazon|audible)\.(co\.\w+|\w+\.\w+|\w+)$/);
    if (!domainMatch) return null;

    const domain = `${domainMatch[1]}.${domainMatch[2]}`;
    return m[domain] || null;
};

    const extractEmail = md => {
        if (!md || typeof md !== 'string') return '';
        const m = md.match(/\[(.*?)]/);
        return m ? m[1] : md;
    };

    function createHamburgerMenu() {
        if (document.getElementById('audible-autologin-hamburger')) return;

        const btn = document.createElement('div');
        btn.id = 'audible-autologin-hamburger';
        Object.assign(btn.style, {
            position: 'fixed', top: '10px', right: '10px', zIndex: 9999,
            width: '30px', height: '30px', background: '#000', color: '#fff',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            borderRadius: '7px', cursor: 'pointer', fontSize: '20px',
        });
        btn.textContent = '≡';

        const panel = document.createElement('div');
        panel.id = 'audible-autologin-panel';
        Object.assign(panel.style, {
            display: 'none', position: 'fixed', top: '50px', right: '10px', zIndex: 9998,
            flexDirection: 'column', gap: '5px', background: '#111', padding: '10px',
            borderRadius: '6px', boxShadow: '0 2px 10px rgba(0,0,0,0.4)'
        });

        ['RNB','Member','3 Days Old'].forEach(type => {
            const b = document.createElement('button');
            b.textContent = type;
            Object.assign(b.style, buttonStyle());
            b.onclick = () => performLogin(type);
            panel.appendChild(b);
        });

        const relogBtn = document.createElement('button');
        relogBtn.textContent = 'Relogin';
        Object.assign(relogBtn.style, buttonStyle());
        relogBtn.onclick = async () => {
            await loginFromLastUsed();
        };
        panel.appendChild(relogBtn);

        const lastUsedBtn = document.createElement('button');
        lastUsedBtn.textContent = 'Last Used';
        Object.assign(lastUsedBtn.style, buttonStyle());
        lastUsedBtn.onclick = async () => {
            try {
                const r = await fetch('http://127.0.0.1:5000/last_used_account');
                const acc = await r.json();
                if (acc.error) return alert(acc.error);
                const msg = `Customer ID: ${acc['Customer ID']}\nEmail: ${acc['Email']}\nPassword: ${acc['Password']}`;
                await navigator.clipboard.writeText(msg);
                alert(msg + "\n(Copied to clipboard)");
            } catch (e) {
                alert('Failed to fetch last used account');
                console.error(e);
            }
        };
        panel.appendChild(lastUsedBtn);

        document.body.appendChild(panel);
        document.body.appendChild(btn);

        btn.onclick = () => {
            panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
        };
    }

    function buttonStyle() {
        return {
            padding: '6px 10px', background: '#222', color: '#fff',
            border: '1px solid #fff', borderRadius: '3px', cursor: 'pointer', fontSize: '12px'
        };
    }

    async function performLogin(type) {
        const mkt = host2Mkt(location.hostname);
        if (!mkt) return alert('Unsupported marketplace');

        try {
            const r = await fetch(`http://127.0.0.1:5000/accounts?marketplace=${mkt}&type=${type.toLowerCase()}`);
            const arr = await r.json();
            if (!arr.length) return alert('No creds from API');

            const { Email: rawEmail, Password: password, "Customer ID": customer_id } = arr[0];
            const email = extractEmail(rawEmail);

            await fillAndSubmitLogin(email, password);
        } catch (e) {
            console.error(e);
            alert('Login failed: ' + e);
        }
    }

    async function loginFromLastUsed() {
        try {
            const r = await fetch('http://127.0.0.1:5000/last_used_account');
            const acc = await r.json();
            if (acc.error) return alert(acc.error);

            const { Email: rawEmail, Password: password } = acc;
            const email = extractEmail(rawEmail);

            await fillAndSubmitLogin(email, password);
        } catch (e) {
            console.error(e);
            alert('Relogin failed: ' + e);
        }
    }

    async function fillAndSubmitLogin(email, password) {
        if (window.location.href.includes('/ap/register')) return;

        const emailInput = await waitFor("form[name='signIn'] input[name='email'], form[name='signIn'] #ap_email");
        emailInput.value = email;
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        (document.querySelector("form[name='signIn'] input#continue, form[name='signIn'] button#continue") || emailInput.form.querySelector('input[type=submit]')).click();

        try {
            const pw = await waitFor("form[name='signIn'] input[name='password'], form[name='signIn'] #ap_password", 8000);
            pw.value = password;
            pw.dispatchEvent(new Event('input', { bubbles: true }));
            (document.querySelector("form[name='signIn'] input#signInSubmit, form[name='signIn'] button#signInSubmit") || pw.form.querySelector('input[type=submit]')).click();
        } catch (e) {
            console.warn('Password screen might not be reached yet:', e);
        }
    }

    if (document.readyState !== 'loading') {
        createHamburgerMenu();
    } else {
        window.addEventListener('DOMContentLoaded', () => {
            createHamburgerMenu();
        });
    }

})();
