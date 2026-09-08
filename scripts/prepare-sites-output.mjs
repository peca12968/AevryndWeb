import { copyFile, mkdir } from 'node:fs/promises';

await mkdir('dist/server', { recursive: true });
await copyFile('dist/aevrynd_engine_journey/index.js', 'dist/server/index.js');
