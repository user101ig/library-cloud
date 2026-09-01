// Βασικές ρυθμίσεις του Node-RED runtime.
module.exports = {
  flowFile: "flows.json",
  credentialSecret: process.env.NODE_RED_CREDENTIAL_SECRET,
  functionExternalModules: true,
  editorTheme: {
    page: { title: "Library Cloud Flows" },
    header: { title: "Library Cloud Flows" }
  }
};
