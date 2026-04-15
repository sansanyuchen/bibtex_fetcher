document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('search-form');
    const input = document.getElementById('paper-title');
    const btn = document.getElementById('search-btn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const errorMsg = document.getElementById('error-message');

    // Result elements
    const arxivCode = document.getElementById('arxiv-bibtex');
    const scholarCode = document.getElementById('scholar-bibtex');
    const arxivCard = document.querySelector('.arxiv-card');
    const scholarCard = document.querySelector('.scholar-card');

    // Copy buttons
    const copyBtns = document.querySelectorAll('.copy-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const title = input.value.trim();
        if (!title) return;

        // UI Reset
        results.classList.add('hidden');
        errorMsg.classList.add('hidden');
        loading.classList.remove('hidden');
        btn.disabled = true;

        arxivCode.textContent = '';
        scholarCode.textContent = '';
        arxivCard.classList.remove('not-found');
        scholarCard.classList.remove('not-found');

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title, source: 'both' }) // Default both
            });

            if (!response.ok) {
                throw new Error('Search failed. Please try again.');
            }

            const data = await response.json();

            // Display Results
            loading.classList.add('hidden');
            results.classList.remove('hidden');

            if (data.arxiv && data.arxiv !== "Not found") {
                arxivCode.textContent = data.arxiv;
            } else {
                arxivCode.textContent = "Citation not found on arXiv.";
                arxivCard.classList.add('not-found');
            }

            if (data.scholar && data.scholar !== "Not found") {
                scholarCode.textContent = data.scholar;
            } else {
                scholarCode.textContent = "Citation not found on Google Scholar.\n(Note: May be rate-limited limit)";
                scholarCard.classList.add('not-found');
            }

        } catch (error) {
            loading.classList.add('hidden');
            errorMsg.textContent = error.message;
            errorMsg.classList.remove('hidden');
        } finally {
            btn.disabled = false;
        }
    });

    // Setup copy to clipboard
    copyBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            const targetId = btn.getAttribute('data-target');
            const targetEl = document.getElementById(targetId);
            const textToCopy = targetEl.textContent;

            if (!textToCopy || targetEl.parentElement.classList.contains('not-found')) return;

            try {
                await navigator.clipboard.writeText(textToCopy);

                // Visual feedback
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.classList.add('copied');

                setTimeout(() => {
                    btn.textContent = originalText;
                    btn.classList.remove('copied');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text: ', err);
            }
        });
    });
});
