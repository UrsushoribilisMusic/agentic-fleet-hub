/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("task_events");

  const metaField = collection.schema.getFieldByName("meta");
  metaField.options.maxSize = 5000;
  collection.schema.addField(metaField);

  return dao.saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("task_events");

  const metaField = collection.schema.getFieldByName("meta");
  metaField.options.maxSize = 0;
  collection.schema.addField(metaField);

  return dao.saveCollection(collection);
});
