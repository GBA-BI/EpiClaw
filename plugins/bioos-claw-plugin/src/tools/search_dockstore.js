import { Type } from "@sinclair/typebox";

import { runCliJson, toTextResult } from "../lib/cli.js";

export function registerSearchDockstoreTool(api) {
  api.registerTool({
    name: "search_dockstore",
    description: "Search workflows from Dockstore.",
    parameters: Type.Object({
      field: Type.String({ minLength: 1, description: "Dockstore search field, such as name, organization, or description." }),
      term: Type.String({ minLength: 1, description: "Search term to match in the selected field." }),
      operator: Type.Optional(Type.String({ default: "AND", description: "Logical operator used to combine query tokens. Defaults to AND." })),
      top_n: Type.Optional(Type.Number({ minimum: 1, description: "Maximum number of search results to return." })),
      query_type: Type.Optional(Type.Union([Type.Literal("match_phrase"), Type.Literal("wildcard")], { description: "Dockstore query mode." })),
      sentence: Type.Optional(Type.Boolean({ description: "Whether to treat the search term as a sentence-level query." })),
      output_full: Type.Optional(Type.Boolean({ description: "Whether to return full result records instead of a compact summary." })),
    }),
    async execute(_id, params) {
      const args = ["--query", params.field, params.operator || "AND", params.term];

      if (params.top_n !== undefined) args.push("--top-n", String(params.top_n));
      if (params.query_type) args.push("--query-type", params.query_type);
      if (params.sentence === true) args.push("--sentence");
      if (params.output_full === true) args.push("--output-full");

      const result = await runCliJson(api, "bioos_dockstore_search", args);
      return toTextResult(result.parsed, `Dockstore search: ${params.field}=${params.term}`);
    },
  });
}
