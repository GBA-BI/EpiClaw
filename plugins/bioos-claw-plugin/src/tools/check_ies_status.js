import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerCheckIesStatusTool(api) {
  api.registerTool({
    name: "check_ies_status",
    description: "Check the status of a Bio-OS IES instance.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that owns the IES instance." }),
      ies_name: Type.String({ minLength: 1, description: "IES instance name to inspect." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--ies-name", params.ies_name);

      const result = await runCliJson(api, "bioos_ies_status", args);
      return toTextResult(result.parsed, `IES status: ${params.workspace_name}/${params.ies_name}`);
    },
  });
}
