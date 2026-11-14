/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4"); // tasks

  // Add reassignment_count
  collection.schema.addField(new SchemaField({
    "id": "reassign_cnt",
    "name": "reassignment_count",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": 0,
      "max": null,
      "noDecimal": true
    }
  }));

  // Add last_reassignment_at
  collection.schema.addField(new SchemaField({
    "id": "last_reassign",
    "name": "last_reassignment_at",
    "type": "date",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": "",
      "max": ""
    }
  }));

  // Update status select field (id: jyzmhpru)
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "jyzmhpru",
    "name": "status",
    "type": "select",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "maxSelect": 1,
      "values": [
        "backlog",
        "todo",
        "in_progress",
        "peer_review",
        "waiting_human",
        "waiting_human_notified",
        "approved",
        "blocked"
      ]
    }
  }));

  return dao.saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  collection.schema.removeField("reassign_cnt");
  collection.schema.removeField("last_reassign");

  // Revert status field (id: jyzmhpru)
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "jyzmhpru",
    "name": "status",
    "type": "select",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "maxSelect": 1,
      "values": [
        "backlog",
        "todo",
        "in_progress",
        "peer_review",
        "waiting_human",
        "approved"
      ]
    }
  }));

  return dao.saveCollection(collection);
});
