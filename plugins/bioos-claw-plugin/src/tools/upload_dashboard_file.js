import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerUploadDashboardFileTool(api) {
  api.registerTool({
    name: "upload_dashboard_file",
    description: "Upload __dashboard__.md to the root of a Bio-OS workspace bucket.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that should receive the dashboard file." }),
      local_file_path: Type.String({ minLength: 1, description: "Absolute local path to the __dashboard__.md file to upload." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--local-file-path", params.local_file_path);

      const result = await runCliJson(api, "bioos_workspace_dashboard_upload", args);
      return toTextResult(result.parsed, `Uploaded dashboard file for: ${params.workspace_name}`);
    },
  });
}
