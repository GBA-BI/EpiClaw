import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerCreateIesappTool(api) {
  api.registerTool({
    name: "create_iesapp",
    description: "Create a new Bio-OS IES application instance.",
    parameters: Type.Object({
      workspace_name: Type.String({ minLength: 1, description: "Workspace name where the IES app should be created." }),
      ies_name: Type.String({ minLength: 1, description: "Name of the new IES application instance." }),
      ies_desc: Type.String({ minLength: 1, description: "Human-readable description of the IES app purpose." }),
      ies_resource: Type.Optional(Type.String({ description: "Optional resource flavor, such as a CPU and memory profile." })),
      ies_storage: Type.Optional(Type.Number({ minimum: 0, description: "Optional persistent storage size in GB." })),
      ies_image: Type.Optional(Type.String({ description: "Optional container image URL to launch inside the IES app." })),
      ies_ssh: Type.Optional(Type.Boolean({ description: "Whether to enable SSH access for the IES instance." })),
      ies_run_limit: Type.Optional(Type.Number({ minimum: 0, description: "Optional maximum runtime limit, in seconds." })),
      ies_idle_timeout: Type.Optional(Type.Number({ minimum: 0, description: "Optional idle timeout before auto-stop, in seconds." })),
      ies_auto_start: Type.Optional(Type.Boolean({ description: "Whether the IES instance should start automatically after creation." })),
    }),
    async execute(_id, params) {
      const args = [];
      args.push("--workspace-name", params.workspace_name);
      args.push("--ies-name", params.ies_name);
      args.push("--ies-desc", params.ies_desc);
      if (params.ies_resource) args.push("--ies-resource", params.ies_resource);
      if (params.ies_storage !== undefined) args.push("--ies-storage", String(params.ies_storage));
      if (params.ies_image) args.push("--ies-image", params.ies_image);
      if (params.ies_ssh === true) args.push("--ies-ssh");
      if (params.ies_ssh === false) args.push("--no-ies-ssh");
      if (params.ies_run_limit !== undefined) args.push("--ies-run-limit", String(params.ies_run_limit));
      if (params.ies_idle_timeout !== undefined) args.push("--ies-idle-timeout", String(params.ies_idle_timeout));
      if (params.ies_auto_start === true) args.push("--ies-auto-start");
      if (params.ies_auto_start === false) args.push("--no-ies-auto-start");

      const result = await runCliJson(api, "bioos_ies_create", args);
      return toTextResult(result.parsed, `Created IES app: ${params.workspace_name}/${params.ies_name}`);
    },
  });
}
