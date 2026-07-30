/**
 * Подготовка релиза: dist/module.json и dist/module.zip.
 *
 *   node tools/release.mjs 1.0.5
 *
 * В манифест подставляются version и download под конкретный тег, тогда как
 * manifest всегда указывает на releases/latest/download/module.json — именно
 * эта пара включает автообновление в Foundry.
 *
 * Внутри архива лежит папка с именем, равным id модуля: Foundry распаковывает
 * релиз в Data/modules/, и без этой обёртки модуль встанет не туда.
 */

import { createWriteStream, existsSync, mkdirSync, readFileSync, readdirSync,
         rmSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { ZipArchive } from "archiver";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const version = process.argv[2]?.replace(/^v/, "");

if (!version || !/^\d+\.\d+\.\d+$/.test(version)) {
  console.error("использование: node tools/release.mjs <версия>, например 1.0.5");
  process.exit(1);
}

function declaredId(name) {
  const manifest = join(ROOT, name, "module.json");
  if (!existsSync(manifest)) return null;
  try {
    return JSON.parse(readFileSync(manifest, "utf8")).id;
  } catch {
    return null;
  }
}

const MODULE_DIR = readdirSync(ROOT, { withFileTypes: true })
  // Каталог модуля — тот, чей module.json объявляет id, равный его имени.
  // По имени опознавать нельзя: рядом остаётся каталог прежней раскладки.
  // По наличию манифеста — тоже: он есть и в dist/ после сборки релиза.
  .filter((e) => e.isDirectory() && declaredId(e.name) === e.name)
  .map((e) => e.name)[0];

const manifestPath = join(ROOT, MODULE_DIR, "module.json");
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));

if (MODULE_DIR !== manifest.id) {
  console.error(`каталог ${MODULE_DIR} не совпадает с id ${manifest.id}`);
  process.exit(1);
}

const repo = process.env.GITHUB_REPOSITORY ?? "nargothrondir/VTM-5e-Compendium";
const base = `https://github.com/${repo}/releases`;

manifest.version = version;
manifest.manifest = `${base}/latest/download/module.json`;
manifest.download = `${base}/download/v${version}/module.zip`;

const dist = join(ROOT, "dist");
rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

// Манифест с подставленной версией существует только в dist и внутри архива.
// Закоммиченный module.json не трогается: версия там правится осознанно, а не
// побочным эффектом сборки, иначе локальный запуск пачкает рабочее дерево.
const rendered = JSON.stringify(manifest, null, 2) + "\n";
writeFileSync(join(dist, "module.json"), rendered);

const zipPath = join(dist, "module.zip");
const output = createWriteStream(zipPath);
const archive = new ZipArchive({ zlib: { level: 9 } });

const done = new Promise((resolve, reject) => {
  output.on("close", resolve);
  archive.on("error", reject);
});

archive.pipe(output);

// Каталог кладётся под именем, равным id модуля, — это и есть та обёртка,
// которую Foundry ожидает увидеть в архиве.
//
// Исключаются: _source (в рантайме не нужен, Foundry читает базу — исходники
// остаются в репозитории), служебные файлы git и сам module.json — вместо
// него ниже кладётся вариант с подставленной версией.
const SKIP = /(^|[\\/])(_source|\.git\w*|module\.json)([\\/]|$)/;
archive.directory(join(ROOT, MODULE_DIR), MODULE_DIR, (entry) =>
  SKIP.test(entry.name) ? false : entry,
);
archive.append(rendered, { name: `${MODULE_DIR}/module.json` });

await archive.finalize();
await done;

console.log(`собран релиз ${version}`);
console.log(`  архив:    ${(archive.pointer() / 1024 / 1024).toFixed(1)} МБ`);
console.log(`  download: ${manifest.download}`);
