export class Playback {
    constructor() {
        this.state = 'stopped'; // playing, paused, stopped
    }

    play() {
        this.state = 'playing';
        console.log("Playback started");
    }

    pause() {
        this.state = 'paused';
        console.log("Playback paused");
    }

    stop() {
        this.state = 'stopped';
        console.log("Playback stopped");
    }
}
