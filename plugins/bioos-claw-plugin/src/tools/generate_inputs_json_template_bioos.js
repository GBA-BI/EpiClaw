import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerGenerateInputsJsonTemplateTool(api) {
  api.registerTool({
    name: "generate_inputs_json_template_bioos",
    description: "Generate the inputs template for a registered Bio-OS workflow.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name that contains the target workflow." }),
      workflow_name: Type.String({ minLength: 1, description: "Workflow name whose inputs template should be generated." }),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--workflow-name", params.workflow_name);

      const result = await runCliJson(api, "bioos_workflow_inputs_template", args);
      return toTextResult(
        result.parsed,
        `Workflow inputs template: ${params.workspace_name}/${params.workflow_name}`,
      );
    },
  });
}
