
// Input Handler (input.js)
// Handles Zoom (Wheel) and Clicks

(function () {
    let zoomLevel = 1.0;

    function setupInput(canvas) {
        // Zoom
        document.addEventListener('wheel', (e) => {
            if (e.ctrlKey) return;
            // Only capture if hovering canvas? Or global?
            // Original was global document listener with passive:false
            e.preventDefault();
            if (e.deltaY < 0) zoomLevel = Math.min(zoomLevel + 0.1, 3.0);
            else zoomLevel = Math.max(zoomLevel - 0.1, 0.5);
        }, { passive: false });

        // Clicks
        canvas.addEventListener('mousedown', (e) => {
            if (!window.GraphicsRenderer) return;

            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;

            const camera = window.GraphicsRenderer.getCameraState();
            const BASE_TILE_SIZE = 64;
            const currentTileSize = Math.round(BASE_TILE_SIZE * zoomLevel);

            // Convert to World Coords
            const tX = Math.floor((mouseX - camera.offsetX) / currentTileSize);
            const tY = Math.floor((mouseY - camera.offsetY) / currentTileSize);

            // Send Move Command
            if (window.gameState && window.gameState.player) {
                const pX = window.gameState.player.xyz[0];
                const pY = window.gameState.player.xyz[1];
                const dx = tX - pX;
                const dy = tY - pY;

                console.log(`Click at ${tX},${tY} (Player: ${pX},${pY}) Delta: ${dx},${dy}`);

                if (Math.abs(dx) + Math.abs(dy) === 1) {
                    if (window.movePlayerCmd) {
                        window.movePlayerCmd({ dx, dy });
                    }
                }
            }
        });
    }

    window.GraphicsInput = {
        setup: setupInput,
        getZoom: () => zoomLevel
    };

})();
