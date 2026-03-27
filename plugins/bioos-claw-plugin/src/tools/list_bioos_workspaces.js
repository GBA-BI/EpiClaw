import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerListBioosWorkspacesTool(api) {
  api.registerTool({
    name: "list_bioos_workspaces",
    description: "List Bio-OS workspaces for the current account.",
    parameters: Type.Object({
      limit: Type.Optional(Type.Number({ minimum: 1, description: "Optional maximum number of workspaces to return." })),
    }),
    async execute(_id, params) {
      const args = [];
      if (params.limit) {
        args.push("--page-size", String(params.limit));
      }

      const result = await runCliJson(api, "bioos_workspace_list", args);
      return toTextResult(result.parsed, "Bio-OS workspaces:");
    },
  });
}
