import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerFetchWdlFromDockstoreTool(api) {
  api.registerTool({
    name: "fetch_wdl_from_dockstore",
    description: "Download workflow files from Dockstore to a local output directory.",
    parameters: Type.Object({
      url: Type.String({ minLength: 1, description: "Dockstore workflow URL or entry path to fetch." }),
      output_path: Type.Optional(Type.String({ description: "Optional absolute local path where the fetched WDL should be saved." })),
    }),
    async execute(_id, params) {
      const args = ["--url", params.url];
      if (params.output_path) args.push("--output-path", params.output_path);

      const result = await runCliJson(api, "bioos_dockstore_wdl_fetch", args);
      return toTextResult(result.parsed, `Dockstore download: ${params.url}`);
    },
  });
}
