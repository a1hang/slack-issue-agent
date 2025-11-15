---
description: Initialize spec from GitHub Issue and create feature branch
tags: [project, kiro, github-flow]
---

# Kiro: Spec from GitHub Issue

Initialize a new specification from a GitHub Issue and automatically create a feature branch for development.

## Workflow

This command automates the GitHub Flow + Spec-Driven Development workflow:

1. **Fetch Issue**: Retrieve GitHub Issue content using `gh` CLI
2. **Initialize Spec**: Run `/kiro:spec-init` with Issue title and description
3. **Create Branch**: Automatically create and checkout feature branch based on generated feature name

## Usage

```
/kiro:spec-from-issue <issue-number>
```

### Arguments

- `issue-number` (required): GitHub Issue number (e.g., `5`, `#5`)

### Example

```
/kiro:spec-from-issue 5
```

This will:

1. Fetch Issue #5 content
2. Initialize spec at `.kiro/specs/<feature-name>/`
3. Create and checkout branch `feature/<feature-name>`

## Instructions for AI

You are responsible for executing the GitHub Flow + Spec-Driven Development workflow. Follow these steps:

### Step 1: Parse Issue Number

Extract the issue number from the user's command:

- Accept formats: `5`, `#5`, `issue-5`
- Validate it's a positive integer

### Step 2: Fetch GitHub Issue

Use `gh` CLI to fetch the issue content:

```bash
gh issue view <issue-number> --json title,body,labels,url
```

**Error Handling**:

- If `gh` is not authenticated: Prompt user to run `gh auth login`
- If issue doesn't exist: Show error and exit
- If API fails: Show error message and exit

### Step 3: Extract and Format Issue Content

From the JSON response, extract:

- `title`: Issue title
- `body`: Issue description (Markdown)
- `labels`: Issue labels (for reference)
- `url`: Issue URL (to include in spec)

**Format for spec-init**:

```
<title>

<body>

GitHub Issue: <url>
```

### Step 4: Initialize Specification

Use the SlashCommand tool to invoke `/kiro:spec-init` with the formatted description:

```typescript
SlashCommand({
  command: '/kiro:spec-init "<formatted-description>"',
});
```

**Important**:

- Escape quotes in the description
- Preserve Markdown formatting
- Include the GitHub Issue URL for traceability

### Step 5: Extract Feature Name

After `/kiro:spec-init` completes, extract the generated feature name from:

- The tool's output message
- Or read from `.kiro/specs/<feature-name>/init.json`

**Feature Name Format**:

- Lowercase, hyphenated (e.g., `aws-infrastructure`, `canvas-integration`)
- No spaces, no special characters except hyphens

### Step 6: Create Feature Branch

Create and checkout a new feature branch:

```bash
git checkout -b feature/<feature-name>
```

**Branch Naming Convention**:

- Prefix: `feature/`
- Name: Use the exact feature name from spec
- Example: `feature/aws-infrastructure`

**Error Handling**:

- If branch already exists: Ask user if they want to switch to it or use a different name
- If there are uncommitted changes: Warn user and ask to commit/stash first

### Step 7: Summary Report

After successful execution, provide a summary:

```markdown
✅ Specification initialized from GitHub Issue #<number>

**Feature**: <feature-name>
**Branch**: feature/<feature-name>
**Spec Location**: .kiro/specs/<feature-name>/
**Issue URL**: <url>

**Next Steps**:

1. Review spec: /kiro:spec-status <feature-name>
2. Generate requirements: /kiro:spec-requirements <feature-name>
3. Create design: /kiro:spec-design <feature-name>
```

## Error Scenarios

Handle these error scenarios gracefully:

1. **Missing gh CLI**:

   ```
   Error: GitHub CLI (gh) is not installed.
   Please install: https://cli.github.com/
   ```

2. **Not authenticated**:

   ```
   Error: GitHub CLI is not authenticated.
   Please run: gh auth login
   ```

3. **Issue not found**:

   ```
   Error: Issue #<number> not found.
   Please verify the issue number and try again.
   ```

4. **Branch already exists**:

   ```
   Warning: Branch feature/<feature-name> already exists.
   Options:
   1. Switch to existing branch: git checkout feature/<feature-name>
   2. Use different name: Please specify a custom branch name
   ```

5. **Uncommitted changes**:
   ```
   Error: You have uncommitted changes.
   Please commit or stash your changes before creating a new branch.
   ```

## Implementation Notes

- **GitHub CLI**: Use `gh issue view` with `--json` flag for structured output
- **SlashCommand Tool**: Use the SlashCommand tool to invoke `/kiro:spec-init`
- **Branch Creation**: Use Bash tool for git operations
- **Error Handling**: Provide clear, actionable error messages
- **Validation**: Validate all inputs before proceeding

## Example Interaction

```
User: /kiro:spec-from-issue 5
```
