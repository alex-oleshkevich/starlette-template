import { LitElement } from 'lit';


export class OnClickOutsideController {
    host: LitElement;

    constructor(host: LitElement, private onOutsideClicked: () => void) {
        (this.host = host).addController(this);
    }

    hostConnected() {
        document.addEventListener('click', this.onDocumentClick.bind(this));
    }

    hostDisconnected() {
        document.removeEventListener('click', this.onDocumentClick.bind(this));
    }

    onDocumentClick(e: MouseEvent) {
        const target = e.target as HTMLElement;
        if (!this.host.contains(target)) {
            this.onOutsideClicked();
        }
    }
}
