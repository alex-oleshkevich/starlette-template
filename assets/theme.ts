import { setCookie } from './cookies';

export type Theme = 'light' | 'dark';

export const CookieName = 'theme';

export const theme = {
    get current(): Theme {
        return (window.document.documentElement.dataset.theme ?? 'light') as Theme;
    },
    setTheme(theme: Theme) {
        window.document.documentElement.dataset.theme = theme;
        setCookie(CookieName, theme, 3600 * 24 * 365);
    },
    toggle() {
        this.setTheme(this.current == 'light' ? 'dark' : 'light');
    }
};
