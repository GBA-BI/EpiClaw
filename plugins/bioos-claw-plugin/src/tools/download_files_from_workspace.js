import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerDownloadFilesFromWorkspaceTool(api) {
  api.registerTool({
    name: "download_files_from_workspace",
    description: "Download files from a Bio-OS workspace to a local path.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the files to download." }),
      sources: Type.Array(
        Type.String({ minLength: 1, description: "One source file path inside the workspace." }),
        { minItems: 1, description: "One or more workspace file paths to download." },
      ),
      target: Type.String({ minLength: 1, description: "Absolute local directory path where downloaded files should be saved." }),
      flatten: Type.Optional(Type.Boolean({ description: "Whether to flatten the downloaded directory structure into the target path." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      for (const source of params.sources) {
        args.push("--source", source);
      }
      args.push("--target", params.target);
      if (params.flatten === true) args.push("--flatten");

      const result = await runCliJson(api, "bioos_workspace_file_download", args);
      return toTextResult(result.parsed, `Downloaded files from: ${params.workspace_name}`);
    },
  });
}
