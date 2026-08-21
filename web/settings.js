export class Settings {
    constructor() {
        this.theme = 'dark';
        this.showGrid = true;
    }

    setTheme(theme) {
        this.theme = theme;
        document.body.className = `theme-${theme}`;
    }
}
