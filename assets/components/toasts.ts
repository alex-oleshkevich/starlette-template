import { LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { Notyf } from 'notyf';

export type ToastType = 'success' | 'error';
export type Toast = {
    message: string,
    category: ToastType,
}

export const toast = new Notyf({
    position: { x: 'center', y: 'bottom' },
    ripple: false,
    duration: 3000,
    dismissible: true,
});

declare global {
    interface HTMLElementTagNameMap {
        'o-toasts': ToastsElement;
    }

    interface DocumentEventMap {
        toast: CustomEvent<Toast>;
    }
}


@customElement('o-toasts')
export class ToastsElement extends LitElement {

    @property({ type: Number })
    duration = 3000;

    private toast: Notyf | null = null;

    protected override firstUpdated() {
        this.toast = new Notyf({
            position: { x: 'center', y: 'bottom' },
            ripple: false,
            duration: this.duration,
            dismissible: true,
        });
        this.displayPendingToasts();
    }

    override connectedCallback() {
        super.connectedCallback();
        document.addEventListener('toast', this.onToast.bind(this));
    }

    override disconnectedCallback() {
        super.disconnectedCallback();
        document.removeEventListener('toast', this.onToast.bind(this));
    }

    private displayPendingToasts() {
        const toasts: Toast[] = JSON.parse(this.textContent || '[]');
        toasts.forEach(toast => this.display(toast));
    }

    show(message: string, category: ToastType = 'success') {
        this.display({ message, category });
    }

    private display(toast: Toast) {
        this.toast?.open({
            type: toast.category,
            message: toast.message,
        });
    }

    onToast(e: CustomEvent<Toast>) {
        this.display(e.detail);
    }

    override render() {
        return null;
    }
}

export const toasts = {
    success(message: string) {
        document.dispatchEvent(new CustomEvent('toast', {
            bubbles: true,
            detail: { message, category: 'success' },
        }));
    },
    error(message: string) {
        document.dispatchEvent(new CustomEvent('toast', {
            bubbles: true,
            detail: { message, category: 'error' },
        }));
    },
};
