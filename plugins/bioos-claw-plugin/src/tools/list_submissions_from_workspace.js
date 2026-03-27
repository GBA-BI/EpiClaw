import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerListSubmissionsFromWorkspaceTool(api) {
  api.registerTool({
    name: "list_submissions_from_workspace",
    description: "List submissions in a Bio-OS workspace.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name whose submissions should be listed." }),
      workflow_name: Type.Optional(Type.String({ description: "Optional workflow name filter." })),
      search_keyword: Type.Optional(Type.String({ description: "Optional keyword used to search submission names or descriptions." })),
      status: Type.Optional(Type.String({ description: "Optional submission status filter, such as Succeeded, Running, or Failed." })),
      page_number: Type.Optional(Type.Number({ minimum: 1, description: "Optional results page number, starting from 1." })),
      page_size: Type.Optional(Type.Number({ minimum: 1, description: "Optional number of submissions to return per page." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);

      if (params.workflow_name) args.push("--workflow-name", params.workflow_name);
      if (params.search_keyword) args.push("--search-keyword", params.search_keyword);
      if (params.status) args.push("--status", params.status);
      if (params.page_number !== undefined) args.push("--page-number", String(params.page_number));
      if (params.page_size !== undefined) args.push("--page-size", String(params.page_size));

      const result = await runCliJson(api, "bioos_workspace_submission_list", args);
      return toTextResult(result.parsed, `Submissions in workspace: ${params.workspace_name}`);
    },
  });
}
