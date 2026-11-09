import type { Plugin as V1Plugin } from "@opencode-ai/plugin";
import type { Plugin } from "@opencode/plugin";
import type { Skill } from "@opencode/schema";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const current_dir = dirname(fileURLToPath(import.meta.url));
const skillsPath = join(current_dir, "skills");
const rulesPath = join(current_dir, "rules", "opencode.md");

/**
 * Parse a skill file's YAML frontmatter without a YAML dependency.
 * Handles the plain, quoted and `|` block-scalar values used by tavily-ai/skills, not general YAML.
 */
function parseSkill(file: string): { name: string; description: string; body: string } {
  const raw = readFileSync(file, "utf8");
  const fence = raw.match(/^---\n([\s\S]*?)\n---\n?/)!;
  const fields: Record<string, string> = {};
  const lines = fence[1].split("\n");
  for (let i = 0; i < lines.length; i++) {
    const field = lines[i].match(/^([\w-]+):\s*(.*)$/);
    if (!field) continue;
    let value = field[2].trim();
    if (value === "|") {
      const block: string[] = [];
      while (i + 1 < lines.length && (lines[i + 1].startsWith(" ") || lines[i + 1] === "")) {
        block.push(lines[++i].replace(/^ {2}/, ""));
      }
      value = block.join("\n").trim();
    } else if (/^(["']).*\1$/.test(value)) {
      value = value.slice(1, -1);
    }
    fields[field[1]] = value;
  }
  return { name: fields.name, description: fields.description, body: raw.slice(fence[0].length).trim() };
}

/** Bundled skill directories, synced from tavily-ai/skills by scripts/sync-skills.sh. */
function skillFiles(): string[] {
  return readdirSync(skillsPath, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => join(skillsPath, entry.name, "SKILL.md"));
}

export default {
  id: "tavily",
  // V1 calls server(); V2 calls setup(). The hooks use their respective APIs.
  async server() {
    return {
      async config(input) {
        input.instructions ??= [];
        // The V1 SDK's Config type still omits the runtime skills setting.
        const config = input as typeof input & { skills?: { paths?: string[] } };
        config.skills ??= {};
        config.skills.paths ??= [];
        if (!input.instructions.includes(rulesPath)) {
          input.instructions.push(rulesPath);
        }
        if (!config.skills.paths.includes(skillsPath)) {
          config.skills.paths.push(skillsPath);
        }
      },
      "shell.env": async (_input, output) => {
        if (process.env.TAVILY_API_KEY) {
          output.env.TAVILY_API_KEY = process.env.TAVILY_API_KEY;
        }
      },
    };
  },
  async setup(ctx) {
    const skills = skillFiles().map((path) => ({ path, ...parseSkill(path) }));
    await ctx.skill.transform((editor) => {
      for (const { path, name, description, body } of skills) {
        editor.add({
          id: name as Skill.ID,
          name: name as Skill.Name,
          description,
          path: path as Skill.Info["path"],
          content: body,
        });
      }
    });

    const rules = readFileSync(rulesPath, "utf8");
    await ctx.session.hook("context", (event) => {
      event.system.push({ type: "text", text: rules });
    });

    await ctx.shell.hook("create.before", (event) => {
      if (process.env.TAVILY_API_KEY) {
        event.env.TAVILY_API_KEY = process.env.TAVILY_API_KEY;
      }
    });
  },
} satisfies Plugin.Plugin & { server: V1Plugin };
