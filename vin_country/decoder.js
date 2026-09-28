// Разбор VIN: страна сборки, регион, производитель, год, контрольный разряд.

const ALLOWED = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789";

// Коды года выпуска (позиция 10), цикл 30 лет.
const YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789";

// Транслитерация для контрольного разряда
const TRANSLIT = {
  A: 1, B: 2, C: 3, D: 4, E: 5, F: 6, G: 7, H: 8,
  J: 1, K: 2, L: 3, M: 4, N: 5, P: 7, R: 9,
  S: 2, T: 3, U: 4, V: 5, W: 6, X: 7, Y: 8, Z: 9,
};
const WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2];

function normalize(raw) {
  return (raw || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
}

function seqIndex(ch) {
  return SEQ.indexOf(ch);
}

function findRegion(ch) {
  const r = REGIONS.find((x) => x.chars.includes(ch));
  return r ? r.name : null;
}

// Страна по первым двум символам
function findCountry(vin) {
  const c1 = vin[0];
  const c2 = vin[1];
  for (const [range, country, iso] of COUNTRY_RANGES) {
    if (range[0] !== c1) continue;
    const lo = seqIndex(range[1]);
    const hi = seqIndex(range[4]);
    const v = seqIndex(c2);
    if (v < 0 || lo < 0 || hi < 0) continue;
    if (v >= lo && v <= hi) return { country, iso, range };
  }
  return null;
}

// Флаг-эмодзи из ISO-кода
function flag(iso) {
  if (!iso || iso.length !== 2) return "";
  return String.fromCodePoint(
    ...[...iso].map((c) => 0x1f1e6 + c.charCodeAt(0) - 65)
  );
}

function decodeYear(vin) {
  const code = vin[9];
  const idx = YEAR_CODES.indexOf(code);
  if (idx < 0) return { text: "не определён", codes: [] };
  const years = [1980 + idx, 2010 + idx].filter((y) => y <= 2031);
  // Для Северной Америки 7-я позиция разводит циклы:
  // буква -> 2010+, цифра -> 1980..2009
  const p7 = vin[6];
  const isNA = "12345".includes(vin[0]);
  if (isNA && /[A-Z]/.test(p7)) return { text: String(years[1]), codes: years };
  if (isNA && /[0-9]/.test(p7)) return { text: String(years[0]), codes: years };
  return { text: years.join(" или "), codes: years };
}

function checkDigit(vin) {
  let sum = 0;
  for (let i = 0; i < 17; i++) {
    const ch = vin[i];
    const val = /[0-9]/.test(ch) ? Number(ch) : TRANSLIT[ch];
    if (val === undefined) return null;
    sum += val * WEIGHTS[i];
  }
  const rem = sum % 11;
  return rem === 10 ? "X" : String(rem);
}

function decodeVin(raw) {
  const vin = normalize(raw);
  const errors = [];

  if (vin.length !== 17) {
    errors.push(`Длина ${vin.length} символов, нужно ровно 17`);
  }
  const bad = [...vin].filter((c) => !ALLOWED.includes(c));
  if (bad.length) {
    errors.push(`Недопустимые символы: ${[...new Set(bad)].join(", ")} (I, O, Q в VIN не используются)`);
  }
  if (errors.length) return { vin, ok: false, errors };

  const region = findRegion(vin[0]);
  const hit = findCountry(vin);
  const wmi = vin.slice(0, 3);
  const maker = WMI[wmi] || null;
  const year = decodeYear(vin);

  const expected = checkDigit(vin);
  const actual = vin[8];
  const naOrCn = "12345L".includes(vin[0]);
  const check = {
    expected,
    actual,
    valid: expected !== null && expected === actual,
    required: naOrCn,
  };

  return {
    vin,
    ok: true,
    errors: [],
    wmi,
    vds: vin.slice(3, 9),
    vis: vin.slice(9),
    region: region || "не определён",
    country: hit ? hit.country : null,
    iso: hit ? hit.iso : null,
    range: hit ? hit.range : null,
    maker: maker ? maker[0] : null,
    makerCountry: maker ? maker[1] : null,
    plant: vin[10],
    serial: vin.slice(11),
    year,
    check,
  };
}
