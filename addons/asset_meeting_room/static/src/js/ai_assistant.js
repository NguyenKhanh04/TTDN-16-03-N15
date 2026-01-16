/** @odoo-module **/

console.log("AI Assistant JS Loaded (Aggressive Focus Version)");

/**
 * Helper to aggressively restore focus to the query input
 * Runs repeatedly for a short duration to handle Odoo's asynchronous re-rendering
 */
function aggressiveFocus() {
    let attempts = 0;
    const maxAttempts = 20; // Try for 2 seconds (100ms * 20)

    const intervalId = setInterval(() => {
        attempts++;
        const queryInput = document.querySelector('input[name="query"]');

        if (queryInput) {
            // Check if we are in the correct context (Assistant Modal/Form)
            const form = queryInput.closest('.o_form_view') || queryInput.closest('.modal-content');

            // Only focus if not already focused
            if (document.activeElement !== queryInput) {
                try {
                    queryInput.focus();
                } catch (err) {
                    console.error("AI Assistant Focus Error:", err);
                }
            }

            // --- Auto Scroll Logic ---
            const chatContainer = document.querySelector('.o_chat_container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }

        if (attempts >= maxAttempts) {
            clearInterval(intervalId);
        }
    }, 100); // Check every 100ms
}

document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter') {
        const target = ev.target;
        // Check if the focused element is our query input
        if (target && target.tagName === 'INPUT' && (target.name === 'query' || target.getAttribute('name') === 'query')) {
            // Find the closest form or modal to ensure we are in the right context
            const modal = target.closest('.modal');
            const form = target.closest('.o_form_view');

            // We want to trigger action_send in our specific assistant
            if (modal || form) {
                const sendButton = (modal || form).querySelector('button[name="action_send"]');
                if (sendButton) {
                    console.log("AI Assistant: Enter detected, clicking send button");
                    ev.preventDefault();
                    ev.stopPropagation();
                    sendButton.click();

                    // Trigger aggressive refocusing after click
                    console.log("AI Assistant: Triggering aggressive refocus...");
                    aggressiveFocus();
                }
            }
        }
    }
}, true); // Use capture phase

// Also listen for clicks on the Send button directly (in case user clicks manually)
document.addEventListener('click', function (ev) {
    const target = ev.target;
    // Check if clicked element is (or is inside) the Send button
    const btn = target.closest('button[name="action_send"]');
    if (btn) {
        // Double check context
        const form = btn.closest('.o_form_view') || btn.closest('.modal-content');
        if (form && form.querySelector('input[name="query"]')) {
            console.log("AI Assistant: Send Clicked, triggering aggressive refocus...");
            aggressiveFocus();
        }
    }
}, true);
