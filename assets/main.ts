import 'flowbite';
import { toasts } from './components';
import { theme } from './theme';

const app = {
    toasts, theme,
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
