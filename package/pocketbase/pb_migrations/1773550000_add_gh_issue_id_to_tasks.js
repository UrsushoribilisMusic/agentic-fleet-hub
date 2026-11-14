/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4"); // tasks

  collection.schema.addField(new SchemaField({
    "id": "gh1s5u3e9",
    "name": "gh_issue_id",
    "type": "number",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "min": null,
      "max": null,
      "noDecimal": true
    }
  }));

  return dao.saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  collection.schema.removeField("gh1s5u3e9");

  return dao.saveCollection(collection);
});
