/// <reference path="../pb_data/types.d.ts" />
// FCP-3: add roster + council_state fields to goals collection so the coordinator
// can track per-goal agent selection and internal state without a separate table.

function jsonField(id, name) {
  return new SchemaField({
    system: false,
    id: id,
    name: name,
    type: "json",
    required: false,
    presentable: false,
    unique: false,
    options: { maxSize: 2000000 },
  });
}

function replaceField(collection, field) {
  try {
    const existing = collection.schema.getFieldByName(field.name);
    field.id = existing.id;
  } catch (_) {
    // field does not exist yet
  }
  collection.schema.addField(field);
}

migrate(
  (db) => {
    const dao = new Dao(db);
    let goals;
    try {
      goals = dao.findCollectionByNameOrId("goals");
    } catch (_) {
      return; // goals collection not present yet; FCP-2 migration must run first
    }

    // roster: JSON array of agent heartbeatKeys e.g. ["clau","gem","codi"]
    replaceField(goals, jsonField("goal_roster", "roster"));

    // council_state: internal coordinator state machine snapshot
    // { "r1_created_at": "ISO", "r2_created_at": "ISO",
    //   "synthesis_created_at": "ISO", "timed_out_rounds": [] }
    replaceField(goals, jsonField("goal_cstate", "council_state"));

    dao.saveCollection(goals);
  },
  (db) => {
    const dao = new Dao(db);
    let goals;
    try {
      goals = dao.findCollectionByNameOrId("goals");
    } catch (_) {
      return;
    }
    ["goal_roster", "goal_cstate"].forEach((fieldId) => {
      try {
        goals.schema.removeField(fieldId);
      } catch (_) {}
    });
    dao.saveCollection(goals);
  }
);
