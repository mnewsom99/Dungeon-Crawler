class AudioManager {
    constructor() {
        this.sounds = {};
        this.bgm = null;
        this.muted = false;
        this.volume = 0.4;

        // Define Audio Assets
        this.assets = {
            'bgm_dungeon': 'static/audio/bgm_dungeon.ogg',
            'step': 'static/audio/step.ogg',
            'door': 'static/audio/door.ogg',
            'attack': 'static/audio/attack_sword.ogg',
            'hit': 'static/audio/hit_blunt.ogg',
            'coin': 'static/audio/coin.ogg',
            'equip': 'static/audio/equip.ogg',
            'page': 'static/audio/page.ogg',
            'click': 'static/audio/click.ogg',
            'mining': 'static/audio/mining.ogg'
        };

        this.initialized = false;

        // UI Mute Toggle
        this.createMuteToggle();
    }

    createMuteToggle() {
        const container = document.createElement('div');
        container.style.position = 'fixed';
        container.style.bottom = '10px';
        container.style.left = '10px';
        container.style.zIndex = '1000';
        container.style.cursor = 'pointer';
        container.style.padding = '5px 10px';
        container.style.background = 'rgba(0,0,0,0.7)';
        container.style.border = '1px solid #444';
        container.style.color = 'gold';
        container.style.fontFamily = 'monospace';
        container.innerText = '🔊 ON';

        container.onclick = () => this.toggleMute(container);

        document.body.appendChild(container);
    }

    toggleMute(btn) {
        this.muted = !this.muted;
        if (this.muted) {
            btn.innerText = '🔇 OFF';
            if (this.bgm) this.bgm.pause();
        } else {
            btn.innerText = '🔊 ON';
            if (this.bgm) this.bgm.play().catch(e => console.log("Unlock Audio first"));
        }
    }

    async init() {
        if (this.initialized) return;

        console.log("Audio: Loading...");

        // Preload sounds
        for (const [key, src] of Object.entries(this.assets)) {
            const audio = new Audio(src);
            audio.volume = this.volume;
            this.sounds[key] = audio;
        }

        // Setup BGM
        this.bgm = this.sounds['bgm_dungeon'];
        if (this.bgm) {
            this.bgm.loop = true;
            this.bgm.volume = 0.2; // Lower BGM volume
        }

        this.initialized = true;

        // Listen for first interaction to unlock audio context
        const unlock = () => {
            if (!this.muted && this.bgm) {
                this.bgm.play().catch(e => console.log("Audio Autoplay blocked", e));
            }
            document.removeEventListener('click', unlock);
            document.removeEventListener('keydown', unlock);
        };

        document.addEventListener('click', unlock);
        document.addEventListener('keydown', unlock);
    }

    play(name) {
        if (this.muted) return;

        const sound = this.sounds[name];
        if (sound) {
            // Clone node to allow overlapping sounds (e.g. rapid steps)
            if (name !== 'bgm_dungeon') {
                const clone = sound.cloneNode();
                clone.volume = this.volume;
                clone.play().catch(e => { }); // Ignore interaction errors
            }
        } else {
            console.warn(`Audio: Sound '${name}' not found.`);
        }
    }
}

window.audioSystem = new AudioManager();
