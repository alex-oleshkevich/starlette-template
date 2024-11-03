declare global {
    interface HTMLElementTagNameMap {
        'x-modals': HTMLDivElement;
    }
}

export const modals = {
    close() {
        document.querySelectorAll('x-modals > *').forEach((modal) => {
            modal.addEventListener('transitionend', () => {
                modal.remove();
            });
            modal.classList.remove('open');
        });
    }
};


document.addEventListener('htmx:afterSettle', e => {
    const el = e.target as HTMLDivElement;
    if (el.matches('x-modals')) {
        setTimeout(() => {
            el.querySelectorAll('*').forEach(el => {
                el.classList.add('open');
            });
        }, 0);
    }

    el.querySelectorAll('[data-action="modals.close"]').forEach((el) => el.addEventListener('click', modals.close));
});

document.addEventListener('modals-close', modals.close);
