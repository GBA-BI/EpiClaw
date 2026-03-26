import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerExportBioosWorkspaceTool(api) {
  api.registerTool({
    name: "export_bioos_workspace",
    description: "Export Bio-OS workspace metadata to a local path.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name to export." }),
      export_path: Type.String({ minLength: 1, description: "Absolute local file or directory path for the exported metadata." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--export-path", params.export_path);

      const result = await runCliJson(api, "bioos_workspace_export", args);
      return toTextResult(result.parsed, `Exported workspace: ${params.workspace_name}`);
    },
  });
}
