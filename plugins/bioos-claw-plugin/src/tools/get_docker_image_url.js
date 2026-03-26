import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerGetDockerImageUrlTool(api) {
  api.registerTool({
    name: "get_docker_image_url",
    description: "Build the full Docker image URL.",
    parameters: Type.Object({
      repo_name: Type.String({ minLength: 1, description: "Docker repository name." }),
      tag: Type.String({ minLength: 1, description: "Image tag to resolve." }),
      registry: Type.Optional(Type.String({ description: "Optional registry hostname. Omit to use the default registry." })),
      namespace_name: Type.Optional(Type.String({ description: "Optional registry namespace or organization name." })),
    }),
    async execute(_id, params) {
      const args = ["--repo-name", params.repo_name, "--tag", params.tag];
      if (params.registry) args.push("--registry", params.registry);
      if (params.namespace_name) args.push("--namespace-name", params.namespace_name);

      const result = await runCliJson(api, "bioos_docker_image_url", args);
      return toTextResult(result.parsed, `Docker image URL: ${params.repo_name}:${params.tag}`);
    },
  });
}
