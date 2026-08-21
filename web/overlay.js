export class Overlay {
    constructor() {
        this.visible = false;
    }

    show(content) {
        this.visible = true;
        const el = document.getElementById('overlay');
        if (el) {
            el.innerHTML = content;
            el.style.display = 'block';
        }
    }

    hide() {
        this.visible = false;
        const el = document.getElementById('overlay');
        if (el) el.style.display = 'none';
    }
}
