/** Small in-process event bus for the browser integration layer. */
export class EventBus {
    constructor() {
        this.listeners = new Map();
    }

    on(name, listener) {
        if (typeof listener !== 'function') return () => {};
        const listeners = this.listeners.get(name) ?? new Set();
        listeners.add(listener);
        this.listeners.set(name, listeners);
        return () => this.off(name, listener);
    }

    once(name, listener) {
        const unsubscribe = this.on(name, (payload) => {
            unsubscribe();
            listener(payload);
        });
        return unsubscribe;
    }

    off(name, listener) {
        this.listeners.get(name)?.delete(listener);
    }

    emit(name, payload = {}) {
        [...(this.listeners.get(name) ?? [])].forEach((listener) => listener(payload));
    }

    clear() {
        this.listeners.clear();
    }
}
