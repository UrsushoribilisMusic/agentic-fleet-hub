/// <reference path="../pb_data/types.d.ts" />
// Add `muse` to tasks.assigned_agent so Muse Code can receive dispatched work.
//
// Muse was already wired everywhere else — MUSE.md, the fleet_meta.json roster,
// the local ~/.local/bin/muse binary, dispatcher AGENT_COMMANDS and its 20-min
// timeout — but the select field rejected the value ("Invalid value muse"), and
// PocketBase is the only kanban the agents read. The dispatcher's muse entry was
// therefore unreachable code: zero task assignments and zero heartbeats ever.
//
// Only tasks.assigned_agent needs it: heartbeats.agent is a free text field
// with no enum constraint, so heartbeat records already validate.

const NEW_AGENTS = ["muse"];

function extendSelect(dao, collectionName, fieldName, add) {
  let collection;
  try {
    collection = dao.findCollectionByNameOrId(collectionName);
  } catch (_) {
    return;
  }
  const field = collection.schema.getFieldByName(fieldName);
  if (!field || field.type !== "select") {
    return; // never write a `values` key into a non-select field's options
  }
  const existing = field.options.values || [];
  field.options.values = Array.from(new Set([...existing, ...add]));
  collection.schema.addField(field);
  dao.saveCollection(collection);
}

function shrinkSelect(dao, collectionName, fieldName, remove) {
  let collection;
  try {
    collection = dao.findCollectionByNameOrId(collectionName);
  } catch (_) {
    return;
  }
  const field = collection.schema.getFieldByName(fieldName);
  if (!field || field.type !== "select") {
    return;
  }
  const existing = field.options.values || [];
  field.options.values = existing.filter((v) => !remove.includes(v));
  collection.schema.addField(field);
  dao.saveCollection(collection);
}

migrate(
  (db) => {
    const dao = new Dao(db);
    extendSelect(dao, "tasks", "assigned_agent", NEW_AGENTS);
  },
  (db) => {
    const dao = new Dao(db);
    shrinkSelect(dao, "tasks", "assigned_agent", NEW_AGENTS);
  }
);
