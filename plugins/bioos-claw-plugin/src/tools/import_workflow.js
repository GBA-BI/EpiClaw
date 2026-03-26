import { Type } from "@sinclair/typebox";

import { runCliText, toPlainTextResult } from "../lib/cli.js";

export function registerImportWorkflowTool(api) {
  api.registerTool({
    name: "import_workflow",
    description: "Import a workflow into Bio-OS via the bioos workflow import CLI.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name where the workflow should be imported." }),
      workflow_name: Type.String({ minLength: 1, description: "Workflow name to register in Bio-OS." }),
      workflow_source: Type.String({ minLength: 1, description: "Absolute path to a local WDL file, a local workflow directory, or a Git repository URL." }),
      workflow_desc: Type.Optional(Type.String({ description: "Optional human-readable description of the workflow." })),
      main_path: Type.Optional(Type.String({ description: "Main workflow file path. Required when workflow_source points to a directory." })),
      monitor: Type.Optional(Type.Boolean({ description: "Whether to wait and poll until the workflow import completes." })),
      monitor_interval: Type.Optional(Type.Number({ minimum: 0, description: "Polling interval in seconds when monitor is enabled." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace_name", params.workspace_name);
      args.push("--workflow_name", params.workflow_name);
      args.push("--workflow_source", params.workflow_source);
      if (params.workflow_desc) args.push("--workflow_desc", params.workflow_desc);
      if (params.main_path) args.push("--main_path", params.main_path);
      if (params.monitor === true) args.push("--monitor");
      if (params.monitor_interval !== undefined) args.push("--monitor_interval", String(params.monitor_interval));

      const result = await runCliText(api, "bioos_workflow_import", args);
      return toPlainTextResult(result.combined || "No workflow import output returned.", `Imported workflow: ${params.workflow_name}`);
    },
  });
}
