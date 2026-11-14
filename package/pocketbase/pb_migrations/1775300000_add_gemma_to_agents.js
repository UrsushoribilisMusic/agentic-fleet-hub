/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  // Find the assigned_agent field by iterating through schema
  let assignedAgentField = null;
  for (let i = 0; i < collection.schema.length; i++) {
    if (collection.schema[i].name === "assigned_agent") {
      assignedAgentField = collection.schema[i];
      break;
    }
  }

  if (assignedAgentField) {
    // Add "gemma" to the values array if not already present
    if (!assignedAgentField.options.values.includes("gemma")) {
      assignedAgentField.options.values.push("gemma");
    }
  }

  return dao.saveCollection(collection);
}, (db) => {
  const dao = new Dao(db);
  const collection = dao.findCollectionByNameOrId("tw44vd067pqost4");

  // Find the assigned_agent field by iterating through schema
  let assignedAgentField = null;
  for (let i = 0; i < collection.schema.length; i++) {
    if (collection.schema[i].name === "assigned_agent") {
      assignedAgentField = collection.schema[i];
      break;
    }
  }

  if (assignedAgentField) {
    // Remove "gemma" from the values array
    assignedAgentField.options.values = assignedAgentField.options.values.filter(
      value => value !== "gemma"
    );
  }

  return dao.saveCollection(collection);
});