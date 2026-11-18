#!/bin/sh
# Print the Tavily awareness rule without its frontmatter.
f=0
while IFS= read -r line || [ -n "$line" ]; do
  if [ "$f" -ge 2 ]; then
    printf '%s\n' "$line"
  elif [ "$line" = "---" ]; then
    f=$((f + 1))
  fi
done < "${CLAUDE_PLUGIN_ROOT}/rules/tavily-awareness.mdc"
