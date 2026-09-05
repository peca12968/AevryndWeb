import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const sitePath = process.argv[2];
const resultPath = process.argv[3];
if (!sitePath || !resultPath) throw new Error("需要 site.js 與結果輸出路徑。");
const siteSource = fs.readFileSync(sitePath, "utf8");

class FakeClassList {
  constructor(owner) { this.owner = owner; this.values = new Set(); }
  add(...values) { values.forEach(value => this.values.add(value)); this.sync(); }
  remove(...values) { values.forEach(value => this.values.delete(value)); this.sync(); }
  toggle(value, force) {
    const enabled = force === undefined ? !this.values.has(value) : Boolean(force);
    if (enabled) this.values.add(value); else this.values.delete(value);
    this.sync();
    return enabled;
  }
  contains(value) { return this.values.has(value); }
  sync() { this.owner._className = Array.from(this.values).join(" "); }
  replaceFrom(value) { this.values = new Set(String(value).split(/\s+/).filter(Boolean)); }
}

class FakeElement {
  constructor() {
    this.dataset = {};
    this.textContent = "";
    this.dateTime = "";
    this.hidden = false;
    this.children = [];
    this._className = "";
    this.classList = new FakeClassList(this);
  }
  get className() { return this._className; }
  set className(value) { this._className = String(value); this.classList.replaceFrom(value); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; if (this.scrollTop !== undefined) this.scrollTop = 0; }
  querySelector() { return null; }
  querySelectorAll() { return []; }
}

const makeCard = id => {
  const fields = {
    cpu: new FakeElement(), ram: new FakeElement(), gpu: new FakeElement(),
    availability: new FakeElement(), sampled: new FakeElement(), diagnostic: new FakeElement()
  };
  const card = new FakeElement();
  card.dataset.nodeId = id;
  card.querySelector = selector => {
    const metric = selector.match(/^\[data-node-metric="(cpu|ram|gpu)"\]$/)?.[1];
    if (metric) return fields[metric];
    if (selector === "[data-node-availability]") return fields.availability;
    if (selector === "[data-node-sampled]") return fields.sampled;
    if (selector === "[data-node-diagnostic]") return fields.diagnostic;
    return null;
  };
  return { card, fields };
};

const createClock = () => {
  let now = 0;
  let nextId = 1;
  const timers = new Map();
  const setTimeout = (callback, delay = 0) => {
    const id = nextId++;
    timers.set(id, { id, due: now + Math.max(0, Number(delay) || 0), callback });
    return id;
  };
  const clearTimeout = id => timers.delete(id);
  const flush = async () => { for (let index = 0; index < 12; index += 1) await Promise.resolve(); };
  const advanceTo = async target => {
    while (true) {
      const next = Array.from(timers.values()).sort((left, right) => left.due - right.due || left.id - right.id)[0];
      if (!next || next.due > target) break;
      timers.delete(next.id);
      now = next.due;
      next.callback();
      await flush();
    }
    now = target;
    await flush();
  };
  return { setTimeout, clearTimeout, advanceTo, now: () => now, timers };
};

const jsonResponse = (body, options = {}) => ({
  ok: options.status === undefined || (options.status >= 200 && options.status < 300),
  status: options.status ?? 200,
  redirected: options.redirected ?? false,
  headers: { get: name => {
    if (name.toLowerCase() === "content-type") return options.contentType ?? "application/json; charset=utf-8";
    if (name.toLowerCase() === "date") return options.omitDate ? null : (options.date ?? new Date(body?.snapshotAt ?? "2026-09-05T00:00:00.000Z").toUTCString());
    return null;
  } },
  json: async () => {
    if (options.jsonError) throw new SyntaxError("invalid json");
    return body;
  }
});

const snapshot = ({
  snapshotAt = "2026-09-05T00:00:00.000Z",
  localAge = 0,
  taichungAge = 0,
  taoyuanAge = 0,
  localAvailability = "current",
  taichungAvailability = "current",
  taoyuanAvailability = "current",
  cpu = 10
} = {}) => {
  const epoch = Date.parse(snapshotAt);
  const node = (id, age, availability, value) => ({
    id,
    name: id,
    cpuPercent: value,
    ramPercent: 20,
    gpuPercent: 30,
    sampledAt: new Date(epoch - age * 1000).toISOString(),
    stale: availability !== "current",
    availability,
    diagnostic: "可信伺服器採樣"
  });
  return {
    sourceAvailable: true,
    sourceStatus: "current",
    snapshotAt,
    nodes: [
      node("local", localAge, localAvailability, cpu),
      node("taichung", taichungAge, taichungAvailability, cpu + 1),
      node("taoyuan", taoyuanAge, taoyuanAvailability, cpu + 2)
    ],
    activeWork: [], history: [], hardware: [], schedule: null
  };
};

const boot = (plans, options = {}) => {
  const clock = createClock();
  const source = new FakeElement();
  const elements = {
    source,
    sourceStatus: new FakeElement(),
    snapshotTime: new FakeElement(),
    pollStatus: new FakeElement(),
    activeBody: new FakeElement(),
    historyBody: new FakeElement(),
    activeWrap: new FakeElement(),
    historyWrap: new FakeElement(),
    activeEmpty: new FakeElement(),
    historyEmpty: new FakeElement()
  };
  const cards = Object.fromEntries(["local", "taichung", "taoyuan"].map(id => [id, makeCard(id)]));
  Object.values(cards).forEach(({ fields }) => {
    fields.availability.textContent = "current";
    fields.availability.className = "operations-badge is-current";
    fields.cpu.textContent = "9.0%";
  });
  const selectorMap = new Map([
    ["[data-operations-source]", elements.source],
    ["[data-source-status]", elements.sourceStatus],
    ["[data-snapshot-time]", elements.snapshotTime],
    ["[data-poll-status]", elements.pollStatus],
    ["[data-active-body]", elements.activeBody],
    ["[data-history-body]", elements.historyBody],
    ["[data-active-wrap]", elements.activeWrap],
    ["[data-history-wrap]", elements.historyWrap],
    ["[data-active-empty]", elements.activeEmpty],
    ["[data-history-empty]", elements.historyEmpty]
  ]);
  const root = new FakeElement();
  const scheduleCards = {};
  if (options.unified) {
    selectorMap.delete("[data-active-body]");
    const grid = new FakeElement();
    elements.scheduleStatus = new FakeElement();
    for (const id of ["local", "taichung", "taoyuan"]) {
      const card = new FakeElement(); card.dataset.scheduleNode = id;
      card.list = new FakeElement(); card.empty = new FakeElement(); card.count = new FakeElement(); card.hint = new FakeElement();
      card.querySelector = selector => ({ "[data-schedule-list]": card.list, "[data-schedule-empty]": card.empty, "[data-schedule-count]": card.count, "[data-schedule-scroll-hint]": card.hint })[selector] || null;
      card.querySelectorAll = selector => selector.includes("[open]") ? card.list.children.filter(item => item.open) : [];
      scheduleCards[id] = card;
    }
    grid.querySelectorAll = () => Object.values(scheduleCards);
    selectorMap.set("[data-schedule-grid]", grid); selectorMap.set("[data-schedule-status]", elements.scheduleStatus);
  }
  let table;
  if (options.dataTable) selectorMap.set("[data-history-table]", new FakeElement());
  root.dataset.snapshotUrl = "/api/operations/snapshot";
  root.querySelector = selector => {
    if (selectorMap.has(selector)) return selectorMap.get(selector);
    const nodeId = selector.match(/^\[data-node-id="([^"]+)"\]$/)?.[1];
    if (nodeId) return cards[nodeId]?.card ?? null;
    return null;
  };
  root.querySelectorAll = selector => selector === "[data-node-id]" ? Object.values(cards).map(item => item.card) : [];
  let fetchCount = 0;
  let activeFetches = 0;
  let maximumActiveFetches = 0;
  const fetch = (_url, options) => {
    const plan = plans[Math.min(fetchCount, plans.length - 1)];
    fetchCount += 1;
    activeFetches += 1;
    maximumActiveFetches = Math.max(maximumActiveFetches, activeFetches);
    let pending;
    if (plan.kind === "hung") {
      pending = new Promise((_, reject) => options.signal?.addEventListener("abort", () => {
        const error = new Error("aborted"); error.name = "AbortError"; reject(error);
      }, { once: true }));
    } else if (plan.kind === "network") {
      pending = Promise.reject(new TypeError("network failed"));
    } else {
      pending = Promise.resolve(plan.response);
    }
    return pending.finally(() => { activeFetches -= 1; });
  };
  const document = {
    querySelector: selector => selector === "[data-operations-root]" ? root : null,
    createElement: () => new FakeElement()
  };
  const window = {
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
    setInterval: () => 0,
    clearInterval: () => {},
    DataTable: options.dataTable ? class {
      constructor(_element, settings) {
        table = this; this.settings = settings; this.rows = []; this.searchTerm = "保留搜尋"; this.pageIndex = 1;
        this.page = value => { if (value === undefined) return this.pageIndex; this.pageIndex = value; return this; };
        this.page.info = () => ({ pages: 3 }); this.row = { add: row => this.rows.push(row) };
      }
      search(value) { if (value === undefined) return this.searchTerm; this.searchTerm = value; return this; }
      clear() { this.rows = []; return this; }
      draw() { return this; }
    } : null
  };
  vm.runInNewContext(siteSource, {
    window, document, fetch, AbortController, performance: { now: clock.now },
    Date, Number, Map, Set, Array, Math, String, Boolean, Error, TypeError, SyntaxError,
    console, location: { assign: () => {} }
  }, { filename: sitePath });
  return {
    clock, elements, cards, scheduleCards, table,
    fetchCount: () => fetchCount,
    maximumActiveFetches: () => maximumActiveFetches
  };
};

const tests = [];
const test = (name, body) => tests.push({ name, body });

test("hung request aborts and the ten-second cadence recovers without overlap", async () => {
  const app = boot([{ kind: "hung" }, { kind: "response", response: jsonResponse(snapshot()) }]);
  await app.clock.advanceTo(10000);
  assert.equal(app.fetchCount(), 1);
  await app.clock.advanceTo(17999);
  assert.equal(app.fetchCount(), 1);
  await app.clock.advanceTo(18000);
  assert.match(app.elements.pollStatus.textContent, /逾時/);
  await app.clock.advanceTo(20000);
  assert.equal(app.fetchCount(), 2);
  assert.equal(app.maximumActiveFetches(), 1);
});

test("network failure ages trusted nodes at exact boundaries without inventing samples", async () => {
  const initial = snapshot({ localAge: 110, localAvailability: "stale", taichungAge: 25, taoyuanAge: 110, taoyuanAvailability: "stale" });
  const app = boot([{ kind: "response", response: jsonResponse(initial) }, { kind: "network" }, { kind: "network" }]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.taichung.fields.availability.textContent, "current");
  assert.equal(app.cards.taoyuan.fields.availability.textContent, "stale");
  await app.clock.advanceTo(30000);
  assert.equal(app.cards.taichung.fields.availability.textContent, "stale");
  assert.equal(app.cards.taoyuan.fields.availability.textContent, "unavailable");
  assert.equal(app.cards.local.fields.availability.textContent, "stale");
  assert.equal(app.cards.taoyuan.fields.sampled.textContent, "2026-09-05 07:58:10 台北時間 (UTC+8)");
  assert.equal(app.cards.taoyuan.fields.cpu.textContent, "unavailable");
});

test("response Date rather than snapshotAt anchors monotonic disconnection aging", async () => {
  const initial = snapshot({ snapshotAt: "2026-09-04T23:00:00.000Z" });
  initial.nodes.forEach(node => { node.sampledAt = "2026-09-05T00:00:30.000Z"; });
  const app = boot([
    { kind: "response", response: jsonResponse(initial, { date: "Fri, 05 Sep 2026 00:01:00 GMT" }) },
    { kind: "network" }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.taichung.fields.availability.textContent, "stale");
});

test("missing response Date fails current state closed without client wall-clock inference", async () => {
  const app = boot([
    { kind: "response", response: jsonResponse(snapshot(), { omitDate: true }) },
    { kind: "network" }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.local.fields.availability.textContent, "unavailable");
  assert.match(app.elements.pollStatus.textContent, /時間來源.*無法驗證/);
});

test("missing response Date preserves an already stale measured state", async () => {
  const initial = snapshot({ taichungAge: 50, taichungAvailability: "stale" });
  const app = boot([
    { kind: "response", response: jsonResponse(initial, { omitDate: true }) },
    { kind: "network" }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.taichung.fields.availability.textContent, "stale");
  assert.equal(app.cards.taichung.fields.cpu.textContent, "11.0%");
});

test("a response Date older than payload tolerance is not trusted for aging", async () => {
  const initial = snapshot({ snapshotAt: "2026-09-05T00:03:00.000Z" });
  const app = boot([
    { kind: "response", response: jsonResponse(initial, { date: "Sat, 05 Sep 2026 00:00:00 GMT" }) },
    { kind: "network" }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.local.fields.availability.textContent, "unavailable");
  assert.match(app.elements.pollStatus.textContent, /時間來源.*無法驗證/);
});

test("first failed request marks server-rendered current badges unavailable", async () => {
  const app = boot([{ kind: "network" }]);
  await app.clock.advanceTo(10000);
  assert.equal(app.cards.local.fields.availability.textContent, "unavailable");
  assert.equal(app.cards.taichung.fields.availability.textContent, "unavailable");
  assert.equal(app.cards.local.fields.cpu.textContent, "unavailable");
});

test("malformed JSON fails closed and keeps the previous trusted view", async () => {
  const app = boot([
    { kind: "response", response: jsonResponse(snapshot({ cpu: 31 })) },
    { kind: "response", response: jsonResponse(null, { jsonError: true }) }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.local.fields.cpu.textContent, "31.0%");
  assert.equal(app.elements.source.classList.contains("is-unavailable"), true);
  assert.match(app.elements.pollStatus.textContent, /格式/);
});

test("malformed nested work is rejected before replacing trusted state", async () => {
  const malformed = snapshot({ snapshotAt: "2026-09-05T00:00:10.000Z", cpu: 88 });
  malformed.activeWork = [null];
  const app = boot([
    { kind: "response", response: jsonResponse(snapshot({ cpu: 31 })) },
    { kind: "response", response: jsonResponse(malformed) }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.local.fields.cpu.textContent, "31.0%");
  assert.match(app.elements.pollStatus.textContent, /格式/);
});

for (const mutation of [
  model => { model.nodes.pop(); },
  model => { model.nodes[2].id = "taichung"; },
  model => { model.nodes[2].id = 'taoyuan\"] [data-node-id="local'; }
]) {
  test("missing duplicate or unsafe node identity is rejected", async () => {
    const invalid = snapshot();
    mutation(invalid);
    const app = boot([{ kind: "response", response: jsonResponse(invalid) }]);
    await app.clock.advanceTo(10000);
    assert.equal(app.elements.source.classList.contains("is-unavailable"), true);
    assert.match(app.elements.pollStatus.textContent, /格式/);
  });
}

test("valid source-unavailable response clears stale measurements without format failure", async () => {
  const unavailable = {
    sourceAvailable: false,
    sourceStatus: "unavailable：找不到通過驗證的摘要。",
    snapshotAt: null,
    nodes: ["local", "taichung", "taoyuan"].map(id => ({
      id, name: id, cpuPercent: null, ramPercent: null, gpuPercent: null, sampledAt: null,
      stale: true, availability: "unavailable", diagnostic: "來源不可用。"
    })),
    activeWork: [], history: [], hardware: [], schedule: null
  };
  const app = boot([
    { kind: "response", response: jsonResponse(snapshot({ cpu: 64 })) },
    { kind: "response", response: jsonResponse(unavailable) }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.cards.local.fields.cpu.textContent, "unavailable");
  assert.equal(app.cards.local.fields.availability.textContent, "unavailable");
  assert.equal(app.elements.sourceStatus.textContent, unavailable.sourceStatus);
  assert.doesNotMatch(app.elements.pollStatus.textContent, /格式錯誤/);
});

test("redirected HTML is rejected before it can masquerade as a snapshot", async () => {
  const app = boot([{ kind: "response", response: jsonResponse(snapshot(), { redirected: true, contentType: "text/html" }) }]);
  await app.clock.advanceTo(10000);
  assert.equal(app.elements.source.classList.contains("is-unavailable"), true);
  assert.match(app.elements.pollStatus.textContent, /格式|重新登入/);
});

for (const status of [401, 403]) {
  test(`${status} explicitly reports an expired login`, async () => {
    const app = boot([{ kind: "response", response: jsonResponse(null, { status }) }]);
    await app.clock.advanceTo(10000);
    assert.equal(app.elements.source.classList.contains("is-unavailable"), true);
    assert.match(app.elements.pollStatus.textContent, /登入.*失效|重新登入/);
  });
}

test("a later valid response recovers source and measured node values", async () => {
  const app = boot([
    { kind: "response", response: jsonResponse(snapshot({ cpu: 11 })) },
    { kind: "network" },
    { kind: "response", response: jsonResponse(snapshot({ snapshotAt: "2026-09-05T00:00:20.000Z", cpu: 77 })) }
  ]);
  await app.clock.advanceTo(10000);
  await app.clock.advanceTo(20000);
  assert.equal(app.elements.source.classList.contains("is-unavailable"), true);
  await app.clock.advanceTo(30000);
  assert.equal(app.elements.source.classList.contains("is-available"), true);
  assert.equal(app.cards.local.fields.cpu.textContent, "77.0%");
  assert.match(app.elements.pollStatus.textContent, /畫面更新/);
});

test("response shape without trusted server time is rejected", async () => {
  const invalid = snapshot();
  invalid.snapshotAt = "not-a-date";
  const app = boot([{ kind: "response", response: jsonResponse(invalid) }]);
  await app.clock.advanceTo(10000);
  assert.equal(app.elements.source.classList.contains("is-unavailable"), true);
  assert.match(app.elements.pollStatus.textContent, /格式/);
});

for (const [input, expected] of [
  ["2026-09-05T00:00:00.000Z", "2026-09-05 08:00:00 台北時間 (UTC+8)"],
  ["2026-09-05T15:59:59.000Z", "2026-09-05 23:59:59 台北時間 (UTC+8)"],
  ["2026-09-05T16:00:00.000Z", "2026-09-06 00:00:00 台北時間 (UTC+8)"],
  ["2026-12-31T23:59:59.000Z", "2027-01-01 07:59:59 台北時間 (UTC+8)"]
]) {
  test(`Taipei display preserves the source instant at ${input}`, async () => {
    const app = boot([{ kind: "response", response: jsonResponse(snapshot({ snapshotAt: input })) }]);
    await app.clock.advanceTo(10000);
    assert.equal(app.elements.snapshotTime.textContent, expected);
    assert.equal(app.elements.snapshotTime.dateTime, input);
    assert.equal(app.cards.local.fields.sampled.textContent, expected);
    assert.equal(app.cards.local.fields.sampled.dateTime, input);
    assert.equal(app.elements.pollStatus.textContent, `畫面更新：${expected}`);
  });
}

test("history uses catalog title while keeping identity details and epoch order", async () => {
  const model = snapshot();
  model.history = [{ name: "TEST-01", type: "codex", host: "台中", startedAt: "2026-09-04T23:59:59Z", updatedAt: model.snapshotAt, endedAt: model.snapshotAt, status: "completed" }];
  model.schedule = { sourceAvailable: true, stale: false, observedAt: model.snapshotAt, tasks: [], catalog: [{
    id: "TEST-01", nodeId: "taichung", title: "驗證派遣同步", description: "安全摘要", state: "completed", reason: "完成", dependsOn: [],
    assignedAt: "2026-09-04T23:00:00Z", updatedAt: model.snapshotAt, evidence: "來源已核對"
  }] };
  const app = boot([{ kind: "response", response: jsonResponse(model) }]);
  await app.clock.advanceTo(10000);
  const row = app.elements.historyBody.children[0];
  assert.equal(row.children[0].textContent, "驗證派遣同步");
  assert.equal(row.children[0].children[0].children[1].textContent, "TEST-01");
  assert.equal(row.children[2].dataset.order, String(Date.parse(model.history[0].startedAt)));
  assert.match(row.children[2].textContent, /2026-09-05 07:59:59 台北時間/);
});

test("malformed title catalog cannot replace trusted view", async () => {
  const model = snapshot();
  model.schedule = { sourceAvailable: true, stale: false, observedAt: model.snapshotAt, tasks: [], catalog: [null] };
  const app = boot([{ kind: "response", response: jsonResponse(model) }]);
  await app.clock.advanceTo(10000);
  assert.match(app.elements.pollStatus.textContent, /格式/);
});

test("unified task area refreshes progress and preserves generation details without duplicate active table", async () => {
  const model = snapshot();
  const task = { id: "WORK-01", instanceId: "555001", nodeId: "taichung", title: "<script>中文任務</script>", description: "工作", reason: "第一階段", state: "acknowledged", dependsOn: [], assignedAt: model.snapshotAt, updatedAt: model.snapshotAt, evidence: "OWNER 555001" };
  model.schedule = { sourceAvailable: true, stale: false, observedAt: model.snapshotAt, diagnostic: "來源核對", tasks: [task], catalog: [task] };
  const later = structuredClone(model); later.schedule.tasks[0].reason = "第二階段"; later.schedule.tasks[0].state = "running";
  const app = boot([{ kind: "response", response: jsonResponse(model) }, { kind: "response", response: jsonResponse(later) }], { unified: true });
  await app.clock.advanceTo(10000);
  const card = app.scheduleCards.taichung;
  assert.equal(card.list.children.length, 1); assert.equal(card.list.children[0].children[0].children[0].textContent, task.title);
  card.list.children[0].open = true;
  await app.clock.advanceTo(20000);
  assert.equal(card.list.children.length, 1); assert.equal(card.list.children[0].open, true);
  assert.equal(card.list.children[0].children[0].children[1].textContent, "執行中");
  assert.match(card.list.children[0].children[1].children[1].textContent, /第二階段/);
  assert.match(app.elements.scheduleStatus.textContent, /來源核對/);
});

test("past task DataTable preserves search page and five-column epoch timeline on refresh", async () => {
  const model = snapshot(); model.history = [{ name: "完成任務", type: "dispatch", host: "台中", startedAt: model.snapshotAt, updatedAt: model.snapshotAt, endedAt: model.snapshotAt, status: "completed", evidenceSummary: "原始報告" }];
  const app = boot([{ kind: "response", response: jsonResponse(model) }], { dataTable: true, unified: true });
  await app.clock.advanceTo(20000);
  assert.equal(app.table.search(), "保留搜尋"); assert.equal(app.table.page(), 1);
  assert.equal(app.table.rows.length, 1); assert.equal(app.table.rows[0].children.length, 5);
  assert.equal(app.table.rows[0].children[2].dataset.order, String(Date.parse(model.snapshotAt)));
  assert.equal(app.table.settings.order[0][0], 2);
});

test("large independent task lists preserve every task and scroll offset across ten-second refresh", async () => {
  const model = snapshot();
  const tasks = ["taichung", "taoyuan"].flatMap((nodeId, index) => Array.from({ length: index ? 19 : 44 }, (_, id) => ({ id: nodeId + id, instanceId: nodeId + id, nodeId, title: "未終止任務 " + id, description: "保留全部", reason: "等待確認", state: "unconfirmed", dependsOn: [], assignedAt: model.snapshotAt, updatedAt: model.snapshotAt, evidence: "來源" })));
  model.schedule = { sourceAvailable: true, stale: false, observedAt: model.snapshotAt, tasks, catalog: tasks };
  const app = boot([{ kind: "response", response: jsonResponse(model) }], { unified: true });
  await app.clock.advanceTo(10000);
  app.scheduleCards.taichung.list.scrollTop = 440; app.scheduleCards.taoyuan.list.scrollTop = 190;
  await app.clock.advanceTo(20000);
  for (const [node, count, offset] of [["taichung", 44, 440], ["taoyuan", 19, 190]]) {
    const card = app.scheduleCards[node]; assert.equal(card.list.children.length, count); assert.equal(card.count.textContent, String(count));
    assert.equal(card.list.scrollTop, offset); assert.match(card.hint.textContent, new RegExp("全部 " + count + " 筆"));
    assert.equal(card.list.children[count - 1].children[0].children[1].textContent, "狀態待確認");
  }
  assert.equal(app.maximumActiveFetches(), 1);
});

const results = [];
let failures = 0;
for (const entry of tests) {
  try {
    await entry.body();
    results.push({ name: entry.name, status: "passed" });
    console.log(`PASS ${entry.name}`);
  } catch (error) {
    failures += 1;
    results.push({ name: entry.name, status: "failed", error: String(error?.stack || error) });
    console.error(`FAIL ${entry.name}\n${error?.stack || error}`);
  }
}

fs.mkdirSync(path.dirname(resultPath), { recursive: true });
fs.writeFileSync(resultPath, JSON.stringify({ total: results.length, passed: results.length - failures, failed: failures, results }, null, 2));
process.exitCode = failures === 0 ? 0 : 1;
