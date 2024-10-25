export function getCookie(name: string, fallback: string | null = null): string | null {
    const value = document.cookie
        .split('; ')
        .find((row) => row.startsWith(name))?.split('=')[0];
    return value ?? fallback;
}

export function setCookie(name: string, value: string, ttl: number, sameSite: string = 'lax'): void {
    const expires = new Date(Date.now() + ttl);
    console.log(`${ expires }`);
    document.cookie = `${ name }=${ value }; expires=${ expires }; SameSite=${ sameSite }`;
}
