import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerListFilesFromWorkspaceTool(api) {
  api.registerTool({
    name: "list_files_from_workspace",
    description: "List files in a Bio-OS workspace.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name whose files should be listed." }),
      prefix: Type.Optional(Type.String({ description: "Optional workspace path prefix used to filter returned files." })),
      recursive: Type.Optional(Type.Boolean({ description: "Whether to list files recursively under the given prefix." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);

      if (params.prefix) args.push("--prefix", params.prefix);
      if (params.recursive === true) args.push("--recursive");

      const result = await runCliJson(api, "bioos_workspace_file_list", args);
      return toTextResult(result.parsed, `Files in workspace: ${params.workspace_name}`);
    },
  });
}
