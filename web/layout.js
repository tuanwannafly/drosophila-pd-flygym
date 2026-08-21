export class Layout {
    constructor() {
        this.currentLayout = "single"; // single, split_h, split_v
    }

    setLayout(layout) {
        this.currentLayout = layout;
        console.log("Layout set to:", layout);
    }
}
