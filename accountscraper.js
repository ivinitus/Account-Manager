// ==UserScript==
// @name         Export Accounts & Send to DB
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  Export accounts and send to server
// @match        https://omega.corp.amazon.com/viewAccounts
// @icon         https://www.google.com/s2/favicons?sz=64&domain=amazon.com
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    function createButton(text, topOffset, onClick) {
        const btn = document.createElement('button');
        btn.innerText = text;
        btn.style.position = 'fixed';
        btn.style.top = topOffset;
        btn.style.left = '20px';
        btn.style.zIndex = '9999';
        btn.style.padding = '10px 20px';
        btn.style.backgroundColor = '#007BFF';
        btn.style.color = '#fff';
        btn.style.border = 'none';
        btn.style.borderRadius = '5px';
        btn.style.cursor = 'pointer';
        btn.addEventListener('click', onClick);
        document.body.appendChild(btn);
    }

    createButton('Reveal Passwords', '80px', () => {
        document.querySelectorAll('.showHideButton').forEach(btn => btn.click());
        console.log('All passwords revealed');
    });

    createButton('Send to DB', '130px', async () => {
        document.querySelectorAll('.showHideButton').forEach(btn => btn.click());
        await new Promise(resolve => setTimeout(resolve, 2000)); 

        const data = [];
        const rows = document.querySelectorAll('tr[id^="table-row-"]');

        rows.forEach(row => {
            const id = row.id.split('-').pop();

            const emailEl = row.querySelector(`#email-${id} a`);
            const passEl = row.querySelector(`#password-display-${id}`);
            const marketEl = row.querySelector(`#market-place-${id}`);
            const customerEl = row.querySelector(`#encrypted-id-${id}`);
            const dateEl = row.querySelectorAll('td')[5]; 

            if (emailEl && passEl && marketEl && customerEl && dateEl) {
                let marketplace = marketEl.innerText.trim().toLowerCase();
                if (marketplace === 'gb') marketplace = 'uk';

                data.push({
                    email: emailEl.innerText.trim(),
                    password: passEl.innerText.trim(),
                    marketplace,
                    customerId: customerEl.innerText.trim(),
                    type: 'rnb',
                    date: dateEl.innerText.trim()
                });
            }
        });

        if (data.length === 0) {
            alert('No account data found to send.');
            return;
        }

        fetch('http://127.0.0.1:5000/import_accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
    alert(`Imported ${result.inserted} accounts`);
})
        .catch(error => {
            console.error('Error importing accounts:', error);
            alert('Failed to import accounts. See console.');
        });
    });

    createButton('Hard Cancel', '180px', () => {
        const dropdown = document.getElementById("account_actions");
        if (dropdown) {
            dropdown.value = "cancelSubscriptions";
            executeSelectedOperation("cancelSubscriptions");
            console.log("Triggered cancelSubscriptions");

            const confirmButton = document.getElementById("modal-delete-credit_card");
            if (confirmButton) {
                confirmButton.click();
                console.log("Confirmation 'Yes' button clicked.");
            } else {
                console.warn("Confirmation button not found.");
            }
        } else {
            alert("Dropdown not found.");
        }
    });
})();