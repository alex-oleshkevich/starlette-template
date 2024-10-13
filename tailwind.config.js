const colorShades = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950];

function generateColors(color) {
    return Object.fromEntries(
        colorShades.map(shade => [shade, `rgb(var(--o-color-${color}-channels-${shade}) / <alpha-value>)`])
    );
}

module.exports = {
    content: [
        'rvapp/**/*.html',
        'assets/**/*.ts',
    ],
    theme: {
        extend: {
            colors: {
                gray: generateColors('gray'),
                red: generateColors('red'),
                yellow: generateColors('yellow'),
                green: generateColors('green'),
                lime: generateColors('lime'),
                blue: generateColors('blue'),
                emerald: generateColors('emerald'),
                teal: generateColors('teal'),
                slate: generateColors('slate'),
                zinc: generateColors('zinc'),
                neutral: generateColors('neutral'),
                stone: generateColors('stone'),
                orange: generateColors('orange'),
                amber: generateColors('amber'),
                cyan: generateColors('cyan'),
                sky: generateColors('sky'),
                indigo: generateColors('indigo'),
                violet: generateColors('violet'),
                purple: generateColors('purple'),
                fuchsia: generateColors('fuchsia'),
                pink: generateColors('pink'),
                rose: generateColors('rose'),

                border: 'var(--o-border-color);',
                link: 'var(--o-link-color);',
                'primary': 'var(--o-text-primary);',
                'primary-inverse': 'var(--o-text-primary-inverse);',
                'secondary': 'var(--o-text-secondary);',
                'secondary-inverse': 'var(--o-text-secondary-inverse);',
                'tertiary': 'var(--o-text-tertiary);',
                'tertiary-inverse': 'var(--o-text-tertiary-inverse);',

                ring: 'var(--o-input-ring-color);',
                accent: 'var(--o-accent-text);',
                danger: 'var(--o-danger-text);',
                highlight: 'var(--o-highlight);',
                hover: 'var(--o-button-secondary-background-hover)',
                surface1: 'var(--o-surface-background)',
                surface2: 'var(--o-surface2-background)',
                surface3: 'var(--o-surface3-background)',
                surface4: 'var(--o-surface4-background)',
            },
        }
    },
};
