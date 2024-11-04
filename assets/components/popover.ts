import { html, LitElement } from 'lit';
import { customElement, property, queryAssignedElements, state } from 'lit/decorators.js';
import { autoPlacement, autoUpdate, computePosition, offset } from '@floating-ui/dom';
import { Placement } from '@floating-ui/utils';
import { OnClickOutsideController } from '../controllers/click_outside';

declare global {
    interface HTMLElementTagNameMap {
        'o-popover': PopoverElement,
    }
}

@customElement('o-popover')
export class PopoverElement extends LitElement {
    clickOutside = new OnClickOutsideController(this, () => {
        if (this.isOpen) {
            this.close();
        }
    });

    @state()
    isOpen = false;

    @property()
    target: string = '';

    @property()
    trigger: string = '';

    @property()
    placement: Placement = 'bottom-start';

    @property({ type: Number, attribute: 'offset-main-axis' })
    offsetMainAxis = 0;

    @property({ type: Number, attribute: 'offset-cross-axis' })
    offsetCrossAxis = 0;

    @property({ type: Number, attribute: 'offset-alignment-axis' })
    offsetAlignmentAxis = 0;

    @queryAssignedElements({ selector: '*:first-child' })
    triggerEl!: HTMLElement[];

    targetEl!: HTMLElement;

    unmountCallback?: () => void = () => {
    };

    protected override render(): unknown {
        if (this.targetEl) {
            if (this.isOpen) {
                this.targetEl.classList.add('open');
            } else {
                this.targetEl.classList.remove('open');
                this.targetEl.style.left = '';
            }
        }
        return html`
            <slot></slot>
            <slot name="popover"></slot>`;
    }

    protected override firstUpdated() {
        let triggerEl = this.triggerEl[0];
        if (this.trigger) {
            triggerEl = Array.from(document.querySelectorAll<HTMLElement>(this.trigger))[0];
        }
        if (!triggerEl) {
            throw new Error(`Invalid trigger element or does not exist: ${ triggerEl }.`);
        }

        let targetEl = document.querySelector<HTMLElement>(this.target);
        if (!targetEl) {
            throw new Error(`No target element: ${ this.target }`);
        }

        this.targetEl = targetEl;

        triggerEl.addEventListener('click', () => {
            this.isOpen = !this.isOpen;
            if (this.isOpen) {
                this.open();
            } else {
                this.close();
            }
        });

        targetEl.querySelectorAll('.list-menu-item').forEach(el => {
            el.addEventListener('click', () => setTimeout(this.close, 40));
        });
    }

    open() {
        this.mount();
        this.isOpen = true;
    }

    close() {
        this.isOpen = false;
        this.unmount();
    }

    mount() {
        const triggerEl = this.triggerEl[0];
        const targetEl = this.targetEl;
        this.unmountCallback = autoUpdate(triggerEl, targetEl, () => {
            computePosition(triggerEl, targetEl, {
                placement: this.placement,
                middleware: [
                    offset({
                        crossAxis: this.offsetCrossAxis,
                        mainAxis: this.offsetMainAxis,
                        alignmentAxis: this.offsetAlignmentAxis,
                    }),
                    autoPlacement({
                        allowedPlacements: [this.placement],
                    }),
                ],
            })
                .then(({ x, y }) => {
                    Object.assign(targetEl.style, {
                        left: `${ x }px`,
                        top: `${ y }px`,
                    });
                });
        });
    }

    unmount() {
        if (this.unmountCallback) {
            this.unmountCallback();
        }
    }
}
