/// <reference path="../pb_data/types.d.ts" />
// FCP-3: extend task_events.event_type select field with council lifecycle events
// so the Fleet Hub can display council progress without parsing meta JSON.

const COUNCIL_EVENT_TYPES = [
  "council_task_created",
  "council_round1_started",
  "council_round2_started",
  "council_synthesis_created",
  "council_synthesis_started",
  "council_complete",
  "council_waiting_human",
];

migrate(
  (db) => {
    const dao = new Dao(db);
    let collection;
    try {
      collection = dao.findCollectionByNameOrId("task_events");
    } catch (_) {
      return;
    }

    const field = collection.schema.getFieldByName("event_type");
    const existing = field.options.values || [];
    const combined = Array.from(new Set([...existing, ...COUNCIL_EVENT_TYPES]));
    field.options.values = combined;
    collection.schema.addField(field);
    dao.saveCollection(collection);
  },
  (db) => {
    const dao = new Dao(db);
    let collection;
    try {
      collection = dao.findCollectionByNameOrId("task_events");
    } catch (_) {
      return;
    }

    const field = collection.schema.getFieldByName("event_type");
    const existing = field.options.values || [];
    field.options.values = existing.filter((v) => !COUNCIL_EVENT_TYPES.includes(v));
    collection.schema.addField(field);
    dao.saveCollection(collection);
  }
);
