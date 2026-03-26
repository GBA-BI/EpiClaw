import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerDeleteSubmissionTool(api) {
  api.registerTool({
    name: "delete_submission",
    description: "Delete a submission from a Bio-OS workspace.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the submission." }),
      submission_id: Type.String({ minLength: 1, description: "Submission ID to delete." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--submission-id", params.submission_id);

      const result = await runCliJson(api, "bioos_submission_delete", args);
      return toTextResult(result.parsed, `Deleted submission: ${params.submission_id}`);
    },
  });
}
