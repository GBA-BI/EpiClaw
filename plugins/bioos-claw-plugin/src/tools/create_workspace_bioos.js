import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerCreateWorkspaceBioosTool(api) {
  api.registerTool({
    name: "create_workspace_bioos",
    description: "Create a Bio-OS workspace and bind default clusters.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Name of the Bio-OS workspace to create." }),
      workspace_description: Type.String({ minLength: 1, description: "Short description explaining the workspace purpose." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--workspace-description", params.workspace_description);

      const result = await runCliJson(api, "bioos_workspace_create", args);
      return toTextResult(result.parsed, `Created workspace: ${params.workspace_name}`);
    },
  });
}
