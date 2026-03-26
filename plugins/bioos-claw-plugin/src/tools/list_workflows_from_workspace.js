import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerListWorkflowsFromWorkspaceTool(api) {
  api.registerTool({
    name: "list_workflows_from_workspace",
    description: "List workflows in a Bio-OS workspace.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name whose workflows should be listed." }),
      search_keyword: Type.Optional(Type.String({ description: "Optional keyword used to filter workflows by name or description." })),
      page_number: Type.Optional(Type.Number({ minimum: 1, description: "Optional results page number, starting from 1." })),
      page_size: Type.Optional(Type.Number({ minimum: 1, description: "Optional number of workflows to return per page." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);

      if (params.search_keyword) {
        args.push("--search-keyword", params.search_keyword);
      }
      if (params.page_number !== undefined) {
        args.push("--page-number", String(params.page_number));
      }
      if (params.page_size !== undefined) {
        args.push("--page-size", String(params.page_size));
      }

      const result = await runCliJson(api, "bioos_workspace_workflow_list", args);
      return toTextResult(result.parsed, `Workflows in workspace: ${params.workspace_name}`);
    },
  });
}
