import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerValidateWdlTool(api) {
  api.registerTool({
    name: "validate_wdl",
    description: "Validate a WDL file with womtool.",
    parameters: Type.Object({
      wdl_path: Type.String({ minLength: 1, description: "Absolute local path to the WDL file that should be validated." }),
    }),
    async execute(_id, params) {
      const result = await runCliJson(api, "bioos_wdl_validate", ["--wdl-path", params.wdl_path]);
      return toTextResult(result.parsed, `Validated WDL: ${params.wdl_path}`);
    },
  });
}
