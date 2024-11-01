import { html, LitElement } from 'lit';
import { customElement, property, queryAssignedElements } from 'lit/decorators.js';
import { autoPlacement, autoUpdate, computePosition, offset } from '@floating-ui/dom';
import { Placement } from '@floating-ui/utils';

declare global {
    interface HTMLElementTagNameMap {
        'o-popover': PopoverElement,
    }
}

@customElement('o-popover')
export class PopoverElement extends LitElement {
    @property({ reflect: true, type: Boolean })
    open = false;

    @property()
    trigger: string | 'previous' | 'next' = '';

    @queryAssignedElements({ selector: '*:first-child' })
    floatingEl!: HTMLElement[];

    @property()
    placement: Placement = 'bottom';

    @property({ type: Number, attribute: 'offset-main-axis' })
    offsetMainAxis = 0;

    @property({ type: Number, attribute: 'offset-cross-axis' })
    offsetCrossAxis = 0;

    @property({ type: Number, attribute: 'offset-alignment-axis' })
    offsetAlignmentAxis = 0;

    getTrigger(): HTMLElement {
        let trigger: HTMLElement | null;
        switch (this.trigger) {
            case 'previous':
                trigger = this.previousElementSibling as HTMLElement;
                break
            case 'next':
                trigger = this.nextElementSibling as HTMLElement;
                break
            default:
                trigger = document.querySelector(this.trigger);
        }
        if (trigger == null) {
            throw new Error('No trigger.');
        }
        return trigger;
    }

    protected override firstUpdated() {
        const triggered = () => this.open ? this.destroy() : this.setup();
        this.addEventListener('close', () => this.close());

        const trigger = this.getTrigger();
        trigger.addEventListener('click', triggered);
        document.addEventListener('click', e => {
            if (!this.open) {
                return;
            }

            if (trigger?.contains(e.target as HTMLElement)) {
                return;
            }

            if (!this.contains(e.target as HTMLElement)) {
                this.open = false;
            }
        });
        this.renderRoot.querySelectorAll('.list-menu-item').forEach(el => {
            el.addEventListener('click', () => {
                setTimeout(this.close, 40);
            });
        });
    }

    close() {
        this.open = false;
    }

    private setup() {
        this.open = true;
        const triggerEl = this.getTrigger()

        if (this.floatingEl.length == 0) {
            throw new Error('Empty slot.');
        }

        autoUpdate(triggerEl, this.floatingEl[0], () => {
            computePosition(triggerEl, this.floatingEl[0], {
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
                    Object.assign(this.floatingEl[0].style, {
                        left: `${ x }px`,
                        top: `${ y }px`,
                    });
                });
        });
    }

    private destroy() {
        this.open = false;
    }

    override render(): unknown {
        this.floatingEl.forEach(el => el.style.display = this.open ? 'block' : 'none');
        return html`
            <slot></slot>`;
    }
}
