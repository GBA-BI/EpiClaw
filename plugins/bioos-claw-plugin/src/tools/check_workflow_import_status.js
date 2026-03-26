import { Type } from "@sinclair/typebox";

import { runCliText, toPlainTextResult } from "../lib/cli.js";

export function registerCheckWorkflowImportStatusTool(api) {
  api.registerTool({
    name: "check_workflow_import_status",
    description: "Check Bio-OS workflow import status.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the imported workflow." }),
      workflow_id: Type.String({ minLength: 1, description: "Workflow ID returned after import_workflow." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace_name", params.workspace_name);
      args.push("--workflow_id", params.workflow_id);

      const result = await runCliText(api, "bioos_workflow_import_status", args);
      return toPlainTextResult(
        result.combined || "No workflow import status output returned.",
        `Workflow import status: ${params.workflow_id}`,
      );
    },
  });
}
