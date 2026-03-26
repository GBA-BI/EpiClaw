import { Type } from "@sinclair/typebox";

import { runCliText, toPlainTextResult } from "../lib/cli.js";

export function registerCheckWorkflowRunStatusTool(api) {
  api.registerTool({
    name: "check_workflow_run_status",
    description: "Check Bio-OS workflow run status for a submission.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the submission." }),
      submission_id: Type.String({ minLength: 1, description: "Submission ID returned by submit_workflow." }),
      page_size: Type.Optional(Type.Number({ minimum: 0, description: "Optional maximum number of run records to return." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace_name", params.workspace_name);
      args.push("--submission_id", params.submission_id);

      if (params.page_size !== undefined) {
        args.push("--page_size", String(params.page_size));
      }

      const result = await runCliText(api, "bioos_workflow_run_status", args);
      return toPlainTextResult(
        result.combined || "No workflow run status output returned.",
        `Workflow run status: ${params.submission_id}`,
      );
    },
  });
}
