import { Type } from "@sinclair/typebox";

import { runCliText, toPlainTextResult } from "../lib/cli.js";

export function registerGetSubmissionLogsTool(api) {
  api.registerTool({
    name: "get_submission_logs",
    description: "Download workflow submission logs to a local directory.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the submission." }),
      submission_id: Type.String({ minLength: 1, description: "Submission ID whose logs should be downloaded." }),
      output_dir: Type.Optional(Type.String({ description: "Optional absolute local directory where logs should be written." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace_name", params.workspace_name);
      args.push("--submission_id", params.submission_id);
      if (params.output_dir) args.push("--output_dir", params.output_dir);

      const result = await runCliText(api, "bioos_submission_logs", args);
      return toPlainTextResult(
        result.combined || "No submission log output returned.",
        `Submission logs: ${params.submission_id}`,
      );
    },
  });
}
