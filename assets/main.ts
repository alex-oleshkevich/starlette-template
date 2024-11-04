import 'flowbite';
import { toasts, modals } from './components';
import { theme } from './theme';

const app = {
    toasts, theme, modals
};

declare global {
    interface Window {
        app: typeof app;
    }
}

window.app = app;

window.addEventListener('htmx:responseError', (event) => {
    const { detail } = event as CustomEvent;
    if (detail.xhr.status === 500) {
        app.toasts.error('Internal server error');
    }
});
