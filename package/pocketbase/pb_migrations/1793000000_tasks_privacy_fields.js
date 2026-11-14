/// <reference path="../pb_data/types.d.ts" />
// Privacy fields for tasks (v0.6).
//   private: never mirror this task to GitHub (council rounds, confidential work).
//   source:  where the task came from (e.g. "telegram", "council", "github").
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tasks");

  if (!collection.schema.getFieldByName("private")) {
    collection.schema.addField(new SchemaField({
      "id": "flotprivate",
      "name": "private",
      "type": "bool",
      "required": false,
      "presentable": false,
      "unique": false,
      "options": {}
    }));
  }
  if (!collection.schema.getFieldByName("source")) {
    collection.schema.addField(new SchemaField({
      "id": "flotsource0",
      "name": "source",
      "type": "text",
      "required": false,
      "presentable": false,
      "unique": false,
      "options": { "min": null, "max": null, "pattern": "" }
    }));
  }
  return dao.saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tasks");
  collection.schema.removeField("flotprivate");
  collection.schema.removeField("flotsource0");
  return dao.saveCollection(collection);
});
