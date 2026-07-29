/**
 * Круговой прогон сборки: _source -> LevelDB -> _source.
 *
 * Доказывает, что компиляция обратима и ничего не теряет. Сравнение идёт
 * по _id и по смыслу, а не побайтово: имя файла CLI выводит из name записи,
 * а name меняется при переводе, поэтому имена файлов закономерно разъезжаются
 * с содержимым. Порядок ключей и отступы тоже не показательны.
 *
 * Рабочее дерево не трогается — всё происходит во временном каталоге.
 */

import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { compilePack, extractPack } from "@foundryvtt/foundryvtt-cli";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const MODULE_DIR = readdirSync(ROOT, { withFileTypes: true })
  .filter((e) => e.isDirectory() && e.name.startsWith("vampire-the-masquerade"))
  .map((e) => e.name)[0];

const manifest = JSON.parse(
  readFileSync(join(ROOT, MODULE_DIR, "module.json"), "utf8"),
);

/** Каноническая форма записи: ключи по алфавиту, на любой глубине. */
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value).sort().map((k) => [k, canonical(value[k])]),
    );
  }
  return value;
}

function loadById(dir) {
  const byId = new Map();
  for (const file of readdirSync(dir).filter((f) => f.endsWith(".json"))) {
    const data = JSON.parse(readFileSync(join(dir, file), "utf8"));
    if (byId.has(data._id)) {
      throw new Error(`${dir}: _id ${data._id} встречается дважды (${file})`);
    }
    byId.set(data._id, { file, json: JSON.stringify(canonical(data)) });
  }
  return byId;
}

const tmp = mkdtempSync(join(tmpdir(), "vtm-roundtrip-"));
let failed = 0;

try {
  for (const pack of manifest.packs) {
    const source = join(ROOT, MODULE_DIR, pack.path, "_source");
    const db = join(tmp, pack.name, "db");
    const out = join(tmp, pack.name, "out");

    await compilePack(source, db, { log: false });
    await extractPack(db, out, { log: false });

    const before = loadById(source);
    const after = loadById(out);

    const lost = [...before.keys()].filter((id) => !after.has(id));
    const extra = [...after.keys()].filter((id) => !before.has(id));
    const changed = [...before.keys()].filter(
      (id) => after.has(id) && after.get(id).json !== before.get(id).json,
    );

    if (lost.length || extra.length || changed.length) {
      failed++;
      console.error(`::error::пак ${pack.name} не сошёлся после прогона`);
      for (const id of lost) console.error(`  потеряна запись ${id} (${before.get(id).file})`);
      for (const id of extra) console.error(`  лишняя запись ${id} (${after.get(id).file})`);
      for (const id of changed) console.error(`  изменилась запись ${id} (${before.get(id).file})`);
    } else {
      console.log(`  ok  ${pack.name}: ${before.size} записей`);
    }
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

if (failed) {
  console.error(`\nкруговой прогон провален: паков с расхождениями — ${failed}`);
  process.exit(1);
}
console.log("\nкруговой прогон пройден: сборка обратима");
