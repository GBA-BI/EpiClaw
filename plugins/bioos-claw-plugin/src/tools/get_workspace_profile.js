import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerGetWorkspaceProfileTool(api) {
  api.registerTool({
    name: "get_workspace_profile",
    description: "Get a high-level Bio-OS workspace profile for agent planning and analysis.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name to profile." }),
      submission_limit: Type.Optional(Type.Number({ minimum: 1, description: "Maximum number of recent submissions to summarize." })),
      artifact_limit_per_submission: Type.Optional(Type.Number({ minimum: 0, description: "Maximum number of artifacts to include per submission." })),
      sample_rows_per_data_model: Type.Optional(Type.Number({ minimum: 0, description: "Sample row count to include for each workspace data model." })),
      include_artifacts: Type.Optional(Type.Boolean({ description: "Whether to include artifact summaries in the profile." })),
      include_failure_details: Type.Optional(Type.Boolean({ description: "Whether to include failure details for unsuccessful submissions." })),
      include_ies: Type.Optional(Type.Boolean({ description: "Whether to include IES application information in the profile." })),
      include_signed_urls: Type.Optional(Type.Boolean({ description: "Whether to include signed download URLs in the profile output." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);

      if (params.submission_limit !== undefined) {
        args.push("--submission-limit", String(params.submission_limit));
      }
      if (params.artifact_limit_per_submission !== undefined) {
        args.push(
          "--artifact-limit-per-submission",
          String(params.artifact_limit_per_submission),
        );
      }
      if (params.sample_rows_per_data_model !== undefined) {
        args.push(
          "--sample-rows-per-data-model",
          String(params.sample_rows_per_data_model),
        );
      }

      if (params.include_artifacts === true) {
        args.push("--include-artifacts");
      } else if (params.include_artifacts === false) {
        args.push("--no-include-artifacts");
      }

      if (params.include_failure_details === true) {
        args.push("--include-failure-details");
      } else if (params.include_failure_details === false) {
        args.push("--no-include-failure-details");
      }

      if (params.include_ies === true) {
        args.push("--include-ies");
      } else if (params.include_ies === false) {
        args.push("--no-include-ies");
      }

      if (params.include_signed_urls === true) {
        args.push("--include-signed-urls");
      }

      const result = await runCliJson(api, "bioos_workspace_profile", args);
      return toTextResult(result.parsed, `Workspace profile: ${params.workspace_name}`);
    },
  });
}
