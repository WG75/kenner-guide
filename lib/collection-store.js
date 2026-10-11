import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { DEFAULT_LIST_NAME } from "./collection-model.js";

function copyItem(item, accessories, listName) {
  return {
    id: item.id,
    listId: item.listId,
    listName: listName || "",
    figureName: item.figureName,
    figureKey: item.figureKey,
    factory: item.factory,
    mould: item.mould,
    coo: item.coo,
    figureGrade: item.figureGrade,
    photo: item.photo,
    notes: item.notes,
    ownedOn: item.ownedOn,
    savedAt: item.savedAt,
    accessories: accessories
      .filter(row => row.itemId === item.id)
      .sort((a, b) => a.position - b.position)
      .map(row => ({ id: row.id, name: row.name, variant: row.variant, grade: row.grade }))
  };
}

export function createMemoryStore(initial) {
  const db = initial || { members: [], lists: [], items: [], accessories: [] };
  db.members ||= [];
  db.lists ||= [];
  db.items ||= [];
  db.accessories ||= [];

  function listName(listId) {
    const list = db.lists.find(row => row.id === listId);
    return list ? list.name : "";
  }

  function memberLists(memberId) {
    return db.lists.filter(row => row.memberId === memberId);
  }

  async function ensureDefault(memberId) {
    let list = memberLists(memberId).find(row => row.isDefault);
    if (list) return list;
    list = {
      id: crypto.randomUUID(),
      memberId,
      name: DEFAULT_LIST_NAME,
      isDefault: true,
      createdAt: new Date().toISOString()
    };
    db.lists.push(list);
    return list;
  }

  return {
    kind: "memory",
    snapshot() {
      return JSON.parse(JSON.stringify(db));
    },
    async ensureMember(member) {
      const plan = member.plan || "free";
      let row = db.members.find(item => item.id === member.id);
      if (!row) {
        row = { id: member.id, email: member.email || "", plan, createdAt: new Date().toISOString() };
        db.members.push(row);
      } else {
        row.email = member.email || row.email;
        row.plan = plan;
      }
      await ensureDefault(member.id);
      return { ...row };
    },
    async setPlan(memberId, plan) {
      const row = db.members.find(item => item.id === memberId);
      if (row) row.plan = plan;
      return row ? { ...row } : null;
    },
    async getMember(memberId) {
      const row = db.members.find(item => item.id === memberId);
      return row ? { ...row } : null;
    },
    async listsFor(memberId) {
      await ensureDefault(memberId);
      return memberLists(memberId).map(list => ({
        id: list.id,
        name: list.name,
        isDefault: Boolean(list.isDefault),
        createdAt: list.createdAt,
        itemCount: db.items.filter(item => item.listId === list.id).length
      }));
    },
    async createList(memberId, name) {
      const exists = memberLists(memberId).some(list => list.name.toLowerCase() === name.toLowerCase());
      if (exists) return { error: "duplicate_list", message: "You already have a list with that name." };
      const list = {
        id: crypto.randomUUID(),
        memberId,
        name,
        isDefault: false,
        createdAt: new Date().toISOString()
      };
      db.lists.push(list);
      return { list: { id: list.id, name: list.name, isDefault: false, createdAt: list.createdAt, itemCount: 0 } };
    },
    async renameList(memberId, listId, name) {
      const list = memberLists(memberId).find(row => row.id === listId);
      if (!list) return { error: "not_found", message: "That list was not found." };
      if (list.isDefault) return { error: "default_list", message: "Personal Collection keeps its name." };
      const clash = memberLists(memberId).some(row => row.id !== listId && row.name.toLowerCase() === name.toLowerCase());
      if (clash) return { error: "duplicate_list", message: "You already have a list with that name." };
      list.name = name;
      return { list: { id: list.id, name: list.name, isDefault: false } };
    },
    async deleteList(memberId, listId) {
      const list = memberLists(memberId).find(row => row.id === listId);
      if (!list) return { error: "not_found", message: "That list was not found." };
      if (list.isDefault) return { error: "default_list", message: "Personal Collection stays. Delete items from it, or move them." };
      const itemIds = new Set(db.items.filter(item => item.listId === listId).map(item => item.id));
      db.accessories = db.accessories.filter(row => !itemIds.has(row.itemId));
      db.items = db.items.filter(item => item.listId !== listId);
      db.lists = db.lists.filter(row => row.id !== listId);
      return { ok: true };
    },
    async itemsFor(memberId, listId) {
      await ensureDefault(memberId);
      const list = memberLists(memberId).find(row => row.id === listId) || memberLists(memberId).find(row => row.isDefault);
      if (!list) return { items: [] };
      const items = db.items
        .filter(item => item.memberId === memberId && item.listId === list.id)
        .map(item => copyItem(item, db.accessories, list.name));
      return {
        list: { id: list.id, name: list.name, isDefault: Boolean(list.isDefault) },
        items
      };
    },
    async allItems(memberId) {
      await ensureDefault(memberId);
      return db.items
        .filter(item => item.memberId === memberId)
        .map(item => copyItem(item, db.accessories, listName(item.listId)));
    },
    async saveItem(memberId, listId, item) {
      await ensureDefault(memberId);
      const lists = memberLists(memberId);
      const list = lists.find(row => row.id === listId) || lists.find(row => row.isDefault);
      if (!list) return { error: "not_found", message: "That list was not found." };
      const row = {
        id: crypto.randomUUID(),
        memberId,
        listId: list.id,
        ...item,
        savedAt: new Date().toISOString()
      };
      db.items.push(row);
      item.accessories.forEach((accessory, position) => {
        db.accessories.push({ id: crypto.randomUUID(), itemId: row.id, position, ...accessory });
      });
      return { item: copyItem(row, db.accessories, list.name) };
    },
    async updateItem(memberId, itemId, item) {
      const row = db.items.find(entry => entry.id === itemId && entry.memberId === memberId);
      if (!row) return { error: "not_found", message: "That item was not found." };
      Object.assign(row, item);
      db.accessories = db.accessories.filter(entry => entry.itemId !== row.id);
      item.accessories.forEach((accessory, position) => {
        db.accessories.push({ id: crypto.randomUUID(), itemId: row.id, position, ...accessory });
      });
      return { item: copyItem(row, db.accessories, listName(row.listId)) };
    },
    async moveItem(memberId, itemId, listId) {
      const row = db.items.find(entry => entry.id === itemId && entry.memberId === memberId);
      if (!row) return { error: "not_found", message: "That item was not found." };
      const list = memberLists(memberId).find(entry => entry.id === listId);
      if (!list) return { error: "not_found", message: "That list was not found." };
      row.listId = list.id;
      return { item: copyItem(row, db.accessories, list.name) };
    },
    async deleteItem(memberId, itemId) {
      const row = db.items.find(entry => entry.id === itemId && entry.memberId === memberId);
      if (!row) return { error: "not_found", message: "That item was not found." };
      db.items = db.items.filter(entry => entry.id !== itemId);
      db.accessories = db.accessories.filter(entry => entry.itemId !== itemId);
      return { ok: true };
    }
  };
}

export function createFileStore(filePath) {
  let initial = null;
  try {
    initial = JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (err) {
    initial = null;
  }
  const memory = createMemoryStore(initial || undefined);
  const persistKeys = new Set([
    "ensureMember", "setPlan", "createList", "renameList", "deleteList",
    "saveItem", "updateItem", "moveItem", "deleteItem"
  ]);
  return new Proxy(memory, {
    get(target, prop) {
      const value = target[prop];
      if (typeof value !== "function" || !persistKeys.has(prop)) return value;
      return async (...args) => {
        const result = await value.apply(target, args);
        fs.mkdirSync(path.dirname(filePath), { recursive: true });
        fs.writeFileSync(filePath, JSON.stringify(target.snapshot()));
        return result;
      };
    }
  });
}

let singleton = null;

export function getStore() {
  if (singleton) return singleton;
  if (process.env.DATABASE_URL) {
    singleton = createNeonStore(process.env.DATABASE_URL);
  } else if (process.env.MEMBERS_STORE_PATH) {
    singleton = createFileStore(process.env.MEMBERS_STORE_PATH);
  } else {
    singleton = createMemoryStore();
  }
  return singleton;
}

export function resetStoreForTests(store) {
  singleton = store || createMemoryStore();
  return singleton;
}

export function createNeonStore(databaseUrl) {
  let sqlPromise = null;
  let ready = null;

  async function sql() {
    if (!sqlPromise) {
      sqlPromise = import("@neondatabase/serverless").then(({ neon }) => neon(databaseUrl));
    }
    return sqlPromise;
  }

  async function ensureSchema() {
    if (ready) return ready;
    ready = (async () => {
      const query = await sql();
      await query`CREATE TABLE IF NOT EXISTS sw_members (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL DEFAULT '',
        plan TEXT NOT NULL DEFAULT 'free',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      )`;
      await query`CREATE TABLE IF NOT EXISTS sw_lists (
        id TEXT PRIMARY KEY,
        member_id TEXT NOT NULL REFERENCES sw_members(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        is_default BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
      )`;
      await query`CREATE TABLE IF NOT EXISTS sw_items (
        id TEXT PRIMARY KEY,
        member_id TEXT NOT NULL REFERENCES sw_members(id) ON DELETE CASCADE,
        list_id TEXT NOT NULL REFERENCES sw_lists(id) ON DELETE CASCADE,
        figure_name TEXT NOT NULL DEFAULT '',
        figure_key TEXT NOT NULL DEFAULT '',
        factory TEXT NOT NULL DEFAULT '',
        mould TEXT NOT NULL DEFAULT '',
        coo TEXT NOT NULL DEFAULT '',
        figure_grade TEXT NOT NULL DEFAULT '',
        photo TEXT NOT NULL DEFAULT '',
        notes TEXT NOT NULL DEFAULT '',
        owned_on DATE,
        saved_at TIMESTAMPTZ NOT NULL DEFAULT now()
      )`;
      await query`CREATE TABLE IF NOT EXISTS sw_item_accessories (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL REFERENCES sw_items(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        variant TEXT NOT NULL DEFAULT '',
        grade TEXT NOT NULL DEFAULT '',
        position INT NOT NULL DEFAULT 0
      )`;
    })();
    return ready;
  }

  async function ensureDefault(memberId) {
    const query = await sql();
    const existing = await query`SELECT id FROM sw_lists WHERE member_id = ${memberId} AND is_default = true LIMIT 1`;
    if (existing.length) return existing[0].id;
    const id = crypto.randomUUID();
    await query`INSERT INTO sw_lists (id, member_id, name, is_default) VALUES (${id}, ${memberId}, ${DEFAULT_LIST_NAME}, true)`;
    return id;
  }

  async function readItem(itemId) {
    const query = await sql();
    const rows = await query`SELECT sw_items.*, sw_lists.name AS list_name
      FROM sw_items JOIN sw_lists ON sw_lists.id = sw_items.list_id
      WHERE sw_items.id = ${itemId}`;
    if (!rows.length) return null;
    const accessories = await query`SELECT id, name, variant, grade FROM sw_item_accessories
      WHERE item_id = ${itemId} ORDER BY position ASC`;
    return rowToItem(rows[0], accessories);
  }

  return {
    kind: "neon",
    async ensureMember(member) {
      await ensureSchema();
      const query = await sql();
      const plan = member.plan || "free";
      await query`INSERT INTO sw_members (id, email, plan)
        VALUES (${member.id}, ${member.email || ""}, ${plan})
        ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, plan = EXCLUDED.plan`;
      await ensureDefault(member.id);
      const rows = await query`SELECT id, email, plan FROM sw_members WHERE id = ${member.id}`;
      return rows[0];
    },
    async getMember(memberId) {
      await ensureSchema();
      const query = await sql();
      const rows = await query`SELECT id, email, plan FROM sw_members WHERE id = ${memberId}`;
      return rows[0] || null;
    },
    async listsFor(memberId) {
      await ensureSchema();
      await ensureDefault(memberId);
      const query = await sql();
      const rows = await query`SELECT sw_lists.id, sw_lists.name, sw_lists.is_default, sw_lists.created_at,
        (SELECT count(*)::int FROM sw_items WHERE sw_items.list_id = sw_lists.id) AS item_count
        FROM sw_lists WHERE member_id = ${memberId} ORDER BY is_default DESC, created_at ASC`;
      return rows.map(row => ({
        id: row.id,
        name: row.name,
        isDefault: Boolean(row.is_default),
        createdAt: row.created_at,
        itemCount: row.item_count
      }));
    },
    async createList(memberId, name) {
      await ensureSchema();
      const query = await sql();
      const clash = await query`SELECT id FROM sw_lists WHERE member_id = ${memberId} AND lower(name) = lower(${name})`;
      if (clash.length) return { error: "duplicate_list", message: "You already have a list with that name." };
      const id = crypto.randomUUID();
      await query`INSERT INTO sw_lists (id, member_id, name, is_default) VALUES (${id}, ${memberId}, ${name}, false)`;
      return { list: { id, name, isDefault: false, itemCount: 0 } };
    },
    async renameList(memberId, listId, name) {
      await ensureSchema();
      const query = await sql();
      const rows = await query`SELECT id, is_default FROM sw_lists WHERE id = ${listId} AND member_id = ${memberId}`;
      if (!rows.length) return { error: "not_found", message: "That list was not found." };
      if (rows[0].is_default) return { error: "default_list", message: "Personal Collection keeps its name." };
      const clash = await query`SELECT id FROM sw_lists WHERE member_id = ${memberId} AND id <> ${listId} AND lower(name) = lower(${name})`;
      if (clash.length) return { error: "duplicate_list", message: "You already have a list with that name." };
      await query`UPDATE sw_lists SET name = ${name} WHERE id = ${listId}`;
      return { list: { id: listId, name, isDefault: false } };
    },
    async deleteList(memberId, listId) {
      await ensureSchema();
      const query = await sql();
      const rows = await query`SELECT is_default FROM sw_lists WHERE id = ${listId} AND member_id = ${memberId}`;
      if (!rows.length) return { error: "not_found", message: "That list was not found." };
      if (rows[0].is_default) return { error: "default_list", message: "Personal Collection stays. Delete items from it, or move them." };
      await query`DELETE FROM sw_item_accessories WHERE item_id IN (SELECT id FROM sw_items WHERE list_id = ${listId})`;
      await query`DELETE FROM sw_items WHERE list_id = ${listId} AND member_id = ${memberId}`;
      await query`DELETE FROM sw_lists WHERE id = ${listId} AND member_id = ${memberId}`;
      return { ok: true };
    },
    async itemsFor(memberId, listId) {
      await ensureSchema();
      const query = await sql();
      await ensureDefault(memberId);
      const lists = await query`SELECT id, name, is_default FROM sw_lists WHERE member_id = ${memberId}`;
      const list = lists.find(row => row.id === listId) || lists.find(row => row.is_default);
      if (!list) return { items: [] };
      const rows = await query`SELECT * FROM sw_items WHERE member_id = ${memberId} AND list_id = ${list.id} ORDER BY saved_at DESC`;
      const items = [];
      for (const row of rows) {
        const accessories = await query`SELECT id, name, variant, grade FROM sw_item_accessories WHERE item_id = ${row.id} ORDER BY position ASC`;
        items.push(rowToItem({ ...row, list_name: list.name }, accessories));
      }
      return { list: { id: list.id, name: list.name, isDefault: Boolean(list.is_default) }, items };
    },
    async allItems(memberId) {
      await ensureSchema();
      const query = await sql();
      await ensureDefault(memberId);
      const rows = await query`SELECT sw_items.*, sw_lists.name AS list_name
        FROM sw_items JOIN sw_lists ON sw_lists.id = sw_items.list_id
        WHERE sw_items.member_id = ${memberId}`;
      const items = [];
      for (const row of rows) {
        const accessories = await query`SELECT id, name, variant, grade FROM sw_item_accessories WHERE item_id = ${row.id} ORDER BY position ASC`;
        items.push(rowToItem(row, accessories));
      }
      return items;
    },
    async saveItem(memberId, listId, item) {
      await ensureSchema();
      const query = await sql();
      const defaultId = await ensureDefault(memberId);
      const lists = await query`SELECT id, name FROM sw_lists WHERE member_id = ${memberId}`;
      const list = lists.find(row => row.id === listId) || lists.find(row => row.id === defaultId);
      if (!list) return { error: "not_found", message: "That list was not found." };
      const id = crypto.randomUUID();
      await query`INSERT INTO sw_items (
        id, member_id, list_id, figure_name, figure_key, factory, mould, coo, figure_grade, photo, notes, owned_on
      ) VALUES (
        ${id}, ${memberId}, ${list.id}, ${item.figureName}, ${item.figureKey}, ${item.factory}, ${item.mould},
        ${item.coo}, ${item.figureGrade}, ${item.photo}, ${item.notes}, ${item.ownedOn}
      )`;
      for (let position = 0; position < item.accessories.length; position += 1) {
        const accessory = item.accessories[position];
        await query`INSERT INTO sw_item_accessories (id, item_id, name, variant, grade, position)
          VALUES (${crypto.randomUUID()}, ${id}, ${accessory.name}, ${accessory.variant}, ${accessory.grade}, ${position})`;
      }
      return { item: await readItem(id) };
    },
    async updateItem(memberId, itemId, item) {
      await ensureSchema();
      const query = await sql();
      const rows = await query`SELECT id FROM sw_items WHERE id = ${itemId} AND member_id = ${memberId}`;
      if (!rows.length) return { error: "not_found", message: "That item was not found." };
      await query`UPDATE sw_items SET
        figure_name = ${item.figureName}, figure_key = ${item.figureKey}, factory = ${item.factory},
        mould = ${item.mould}, coo = ${item.coo}, figure_grade = ${item.figureGrade},
        photo = ${item.photo}, notes = ${item.notes}, owned_on = ${item.ownedOn}
        WHERE id = ${itemId}`;
      await query`DELETE FROM sw_item_accessories WHERE item_id = ${itemId}`;
      for (let position = 0; position < item.accessories.length; position += 1) {
        const accessory = item.accessories[position];
        await query`INSERT INTO sw_item_accessories (id, item_id, name, variant, grade, position)
          VALUES (${crypto.randomUUID()}, ${itemId}, ${accessory.name}, ${accessory.variant}, ${accessory.grade}, ${position})`;
      }
      return { item: await readItem(itemId) };
    },
    async moveItem(memberId, itemId, listId) {
      await ensureSchema();
      const query = await sql();
      const item = await query`SELECT id FROM sw_items WHERE id = ${itemId} AND member_id = ${memberId}`;
      if (!item.length) return { error: "not_found", message: "That item was not found." };
      const list = await query`SELECT id FROM sw_lists WHERE id = ${listId} AND member_id = ${memberId}`;
      if (!list.length) return { error: "not_found", message: "That list was not found." };
      await query`UPDATE sw_items SET list_id = ${listId} WHERE id = ${itemId}`;
      return { item: await readItem(itemId) };
    },
    async deleteItem(memberId, itemId) {
      await ensureSchema();
      const query = await sql();
      const rows = await query`SELECT id FROM sw_items WHERE id = ${itemId} AND member_id = ${memberId}`;
      if (!rows.length) return { error: "not_found", message: "That item was not found." };
      await query`DELETE FROM sw_item_accessories WHERE item_id = ${itemId}`;
      await query`DELETE FROM sw_items WHERE id = ${itemId}`;
      return { ok: true };
    }
  };
}

function rowToItem(row, accessories) {
  const owned = row.owned_on instanceof Date
    ? row.owned_on.toISOString().slice(0, 10)
    : String(row.owned_on || "").slice(0, 10);
  return {
    id: row.id,
    listId: row.list_id,
    listName: row.list_name || "",
    figureName: row.figure_name,
    figureKey: row.figure_key,
    factory: row.factory,
    mould: row.mould,
    coo: row.coo,
    figureGrade: row.figure_grade,
    photo: row.photo,
    notes: row.notes,
    ownedOn: owned,
    savedAt: row.saved_at,
    accessories: (accessories || []).map(entry => ({
      id: entry.id,
      name: entry.name,
      variant: entry.variant,
      grade: entry.grade
    }))
  };
}
