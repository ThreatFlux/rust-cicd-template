#!/bin/sh
# Install repository hooks without replacing hooks in sibling worktrees.
set -eu

git_dir="$(git rev-parse --absolute-git-dir)"
hooks="$git_dir/template-hooks"
mkdir -p "$hooks"
for specification in pre-commit:pre-commit pre-push:ci-local; do
    hook="${specification%%:*}"
    target="${specification#*:}"
    printf '#!/bin/sh\nset -eu\nexec make %s\n' "$target" > "$hooks/$hook"
    chmod +x "$hooks/$hook"
done

# Git otherwise shares core.hooksPath with every sibling checkout.
git config extensions.worktreeConfig true
git config --worktree core.hooksPath "$hooks"
printf 'Installed hooks for this worktree: %s\n' "$hooks"
