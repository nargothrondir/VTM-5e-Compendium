/**
 * Сборка компендиумов: packs/<pack>/_source/*.json -> база LevelDB.
 *
 * Истина хранится в _source; скомпилированная база — артефакт и в git не
 * попадает. Foundry читает именно базу, поэтому после каждой правки исходников
 * нужно `npm run build`.
 *
 *   npm run build      # _source -> LevelDB
 *   npm run unpack     # LevelDB -> _source (после правок в интерфейсе Foundry)
 */

import { readFileSync, rmSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { compilePack, extractPack } from "@foundryvtt/foundryvtt-cli";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const MODULE_DIR = readdirSync(ROOT, { withFileTypes: true })
  .filter((e) => e.isDirectory() && e.name.startsWith("vampire-the-masquerade"))
  .map((e) => e.name)[0];

if (!MODULE_DIR) {
  console.error("не найден каталог модуля в корне репозитория");
  process.exit(1);
}

const manifest = JSON.parse(
  readFileSync(join(ROOT, MODULE_DIR, "module.json"), "utf8"),
);

const unpack = process.argv.includes("--unpack");

for (const pack of manifest.packs) {
  const dir = join(ROOT, MODULE_DIR, pack.path);
  const source = join(dir, "_source");

  if (unpack) {
    // Имя файла CLI выводит из name записи, а name меняется при переводе.
    // Без очистки рядом со старым файлом ляжет новый — и в _source окажутся
    // две записи с одним _id, из которых сборка возьмёт произвольную.
    rmSync(source, { recursive: true, force: true });
    await extractPack(dir, source, { log: true });
    continue;
  }

  if (!existsSync(source)) {
    console.error(`пропущен ${pack.name}: нет ${source}`);
    continue;
  }

  // Пересборка с нуля: иначе удалённые записи остаются в базе.
  for (const entry of readdirSync(dir)) {
    if (entry !== "_source") rmSync(join(dir, entry), { recursive: true, force: true });
  }

  await compilePack(source, dir, { log: true });
}

console.log(unpack ? "распаковано" : "собрано");
