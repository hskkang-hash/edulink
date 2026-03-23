import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readdirSync,
  rmSync,
  statSync,
} from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(process.cwd());
const distDir = resolve(root, "dist");
const frontendDir = resolve(root, "frontend");
const assetsDir = resolve(root, "assets");

if (!existsSync(frontendDir)) {
  throw new Error("Missing frontend directory. Expected ./frontend");
}

function copyDirectoryRecursive(sourceDir, targetDir) {
  mkdirSync(targetDir, { recursive: true });

  for (const name of readdirSync(sourceDir)) {
    const sourcePath = join(sourceDir, name);
    const targetPath = join(targetDir, name);
    const stats = statSync(sourcePath);

    if (stats.isDirectory()) {
      copyDirectoryRecursive(sourcePath, targetPath);
      continue;
    }

    copyFileSync(sourcePath, targetPath);
  }
}

rmSync(distDir, { recursive: true, force: true });
mkdirSync(distDir, { recursive: true });

copyDirectoryRecursive(frontendDir, distDir);

if (existsSync(assetsDir)) {
  copyDirectoryRecursive(assetsDir, resolve(distDir, "assets"));
}

console.log("Static bundle ready in ./dist");
