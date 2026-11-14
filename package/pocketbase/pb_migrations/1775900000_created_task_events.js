/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const collection = new Collection({
    "id": "task_events_col01",
    "created": "2026-04-05 00:00:00.000Z",
    "updated": "2026-04-05 00:00:00.000Z",
    "name": "task_events",
    "type": "base",
    "system": false,
    "schema": [
      {
        "system": false,
        "id": "te_task_id",
        "name": "task_id",
        "type": "text",
        "required": true,
        "presentable": false,
        "unique": false,
        "options": { "min": null, "max": null, "pattern": "" }
      },
      {
        "system": false,
        "id": "te_event_type",
        "name": "event_type",
        "type": "select",
        "required": true,
        "presentable": false,
        "unique": false,
        "options": {
          "maxSelect": 1,
          "values": [
            "status_transition",
            "reassignment",
            "circuit_breaker",
            "queue_snapshot"
          ]
        }
      },
      {
        "system": false,
        "id": "te_from_status",
        "name": "from_status",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": { "min": null, "max": null, "pattern": "" }
      },
      {
        "system": false,
        "id": "te_to_status",
        "name": "to_status",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": { "min": null, "max": null, "pattern": "" }
      },
      {
        "system": false,
        "id": "te_agent",
        "name": "agent",
        "type": "text",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": { "min": null, "max": null, "pattern": "" }
      },
      {
        "system": false,
        "id": "te_meta",
        "name": "meta",
        "type": "json",
        "required": false,
        "presentable": false,
        "unique": false,
        "options": {}
      },
      {
        "system": false,
        "id": "te_timestamp",
        "name": "timestamp",
        "type": "date",
        "required": true,
        "presentable": false,
        "unique": false,
        "options": { "min": "", "max": "" }
      }
    ],
    "indexes": [
      "CREATE INDEX idx_task_events_task_id ON task_events (task_id)",
      "CREATE INDEX idx_task_events_event_type ON task_events (event_type)",
      "CREATE INDEX idx_task_events_timestamp ON task_events (timestamp)"
    ],
    "listRule": "",
    "viewRule": "",
    "createRule": "",
    "updateRule": null,
    "deleteRule": null,
    "options": {}
  });

  return Dao(db).saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("task_events_col01");
  return dao.deleteCollection(collection);
});
