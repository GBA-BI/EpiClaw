import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerGetIesEventsTool(api) {
  api.registerTool({
    name: "get_ies_events",
    description: "Get events for a Bio-OS IES instance.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that owns the IES instance." }),
      ies_name: Type.String({ minLength: 1, description: "IES instance name whose events should be fetched." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--ies-name", params.ies_name);

      const result = await runCliJson(api, "bioos_ies_events", args);
      return toTextResult(result.parsed, `IES events: ${params.workspace_name}/${params.ies_name}`);
    },
  });
}
