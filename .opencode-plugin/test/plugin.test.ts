import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { afterEach, beforeEach, describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import plugin from "../index.js";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const skillsPath = join(root, "skills");
const rulesPath = join(root, "rules", "opencode.md");
const bundledSkills = readdirSync(skillsPath, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
type V1Config = Parameters<Awaited<ReturnType<typeof plugin.server>>["config"]>[0] & {
  skills?: { paths?: string[] };
};
type V2Context = Parameters<typeof plugin.setup>[0];
type SkillEditor = Parameters<Parameters<V2Context["skill"]["transform"]>[0]>[0];
type SkillInfo = Parameters<SkillEditor["add"]>[0];

function skillEditor(skills: SkillInfo[]): SkillEditor {
  return {
    add(skill) { skills.push(skill); },
    list() { return []; },
    get() { return undefined; },
    update() { throw new Error("Unexpected skill update"); },
    remove() { throw new Error("Unexpected skill removal"); },
  };
}

// Only domains consumed by this plugin are implemented by this test context.
async function setupV2() {
  const skills: SkillInfo[] = [];
  const transforms: Array<(editor: SkillEditor) => void> = [];
  const hooks = new Map<string, (event: unknown) => void | Promise<void>>();
  const registration = { async dispose() {} };
  const context = {
    skill: {
      async transform(callback: (editor: SkillEditor) => void) {
        transforms.push(callback);
        callback(skillEditor(skills));
        return registration;
      },
    },
    session: {
      async hook(name: string, callback: (event: unknown) => void | Promise<void>) {
        hooks.set(`session.${name}`, callback);
        return registration;
      },
    },
    shell: {
      async hook(name: string, callback: (event: unknown) => void | Promise<void>) {
        hooks.set(`shell.${name}`, callback);
        return registration;
      },
    },
  };
  await plugin.setup(context as unknown as V2Context);
  return { skills, transforms, hooks };
}

describe("dual-version plugin", () => {
  let originalKey: string | undefined;
  beforeEach(() => {
    originalKey = process.env.TAVILY_API_KEY;
    delete process.env.TAVILY_API_KEY;
  });
  afterEach(() => {
    if (originalKey === undefined) delete process.env.TAVILY_API_KEY;
    else process.env.TAVILY_API_KEY = originalKey;
  });

  it("default-exports one definition with both version entrypoints", () => {
    assert.equal(plugin.id, "tavily");
    assert.equal(typeof plugin.server, "function");
    assert.equal(typeof plugin.setup, "function");
  });

  it("V1 registers the skills path and OpenCode rules on an empty config", async () => {
    const hooks = await plugin.server();
    const config: V1Config = {};
    await hooks.config(config);
    assert.deepEqual(config.instructions, [rulesPath]);
    assert.deepEqual(config.skills?.paths, [skillsPath]);
  });

  it("V1 preserves existing config and avoids duplicates on repeated calls", async () => {
    const hooks = await plugin.server();
    const config: V1Config = {
      instructions: ["AGENTS.md"],
      skills: { paths: ["./team-skills"] },
    };
    await hooks.config(config);
    await hooks.config(config);
    assert.deepEqual(config.instructions, ["AGENTS.md", rulesPath]);
    assert.deepEqual(config.skills?.paths, ["./team-skills", skillsPath]);
  });

  it("V1 forwards the API key without overwriting unrelated environment variables", async () => {
    const hooks = await plugin.server();
    process.env.TAVILY_API_KEY = "tvly-test-only";
    const output = { env: { KEEP: "value" } as Record<string, string> };
    await hooks["shell.env"]({ cwd: root }, output);
    assert.deepEqual(output.env, { KEEP: "value", TAVILY_API_KEY: "tvly-test-only" });
  });

  it("V1 leaves the environment unchanged when no API key is set", async () => {
    const hooks = await plugin.server();
    const output = { env: { TAVILY_API_KEY: "existing" } };
    await hooks["shell.env"]({ cwd: root }, output);
    assert.deepEqual(output.env, { TAVILY_API_KEY: "existing" });
  });

  it("V2 registers every bundled skill with parsed frontmatter and a replayable transform", async () => {
    const { skills, transforms } = await setupV2();
    assert.ok(bundledSkills.includes("tavily-search"));
    assert.deepEqual(skills.map((skill) => skill.name).sort(), [...bundledSkills].sort());
    for (const skill of skills) {
      assert.equal(skill.id, skill.name);
      assert.equal(skill.path, join(skillsPath, skill.name, "SKILL.md"));
      assert.ok(skill.description);
      assert.doesNotMatch(skill.description, /^["'|]/);
      assert.ok(skill.content);
      assert.doesNotMatch(skill.content, /^---/);
    }
    const replayed: SkillInfo[] = [];
    transforms[0](skillEditor(replayed));
    assert.deepEqual(replayed, skills);
  });

  it("V2 appends the OpenCode rules without removing existing system context", async () => {
    const { hooks } = await setupV2();
    const event = { system: [{ type: "text", text: "Existing instructions" }] };
    await hooks.get("session.context")!(event);
    assert.deepEqual(event.system, [
      { type: "text", text: "Existing instructions" },
      {
        type: "text",
        text: readFileSync(rulesPath, "utf8"),
      },
    ]);
  });

  it("V2 forwards the API key through create.before and preserves other variables", async () => {
    const { hooks } = await setupV2();
    process.env.TAVILY_API_KEY = "tvly-test-only";
    const event = { env: { KEEP: "value" } as Record<string, string> };
    await hooks.get("shell.create.before")!(event);
    assert.deepEqual(event.env, { KEEP: "value", TAVILY_API_KEY: "tvly-test-only" });
  });

  it("V2 leaves the environment unchanged when no API key is set", async () => {
    const { hooks } = await setupV2();
    const event = { env: { TAVILY_API_KEY: "existing" } };
    await hooks.get("shell.create.before")!(event);
    assert.deepEqual(event.env, { TAVILY_API_KEY: "existing" });
  });
});
