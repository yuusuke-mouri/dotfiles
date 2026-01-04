# Claude Code Configuration

Claude Code skills, commands, agents, and hooks.

## Setup

```bash
./install.sh
claude login
```

## Structure

```
claude/
├── skills/      # Custom skills
├── plans/       # Planning documents
├── commands/    # Slash commands (/command-name)
├── agents/      # Subagents
└── hooks/       # Automation hooks
```

## Usage

- **skills/**: Define reusable skills with SKILL.md
- **commands/**: Create slash commands (e.g., /my-command)
- **agents/**: Define custom subagents
- **hooks/**: Automate actions on events
