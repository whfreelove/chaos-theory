# Chaos Theory Plugin Marketplace

A Claude Code plugin marketplace for distributing and managing plugins.

## Installation

Add this marketplace to your Claude Code:

```bash
/plugin marketplace add <your-github-repo>
```

Or if using a local path for development:

```bash
/plugin marketplace add /Users/whfreelove/dev/tenere/chaos-theory
```

## Available Plugins

Currently no plugins are available. Add plugins to the `plugins/` directory and update `.claude-plugin/marketplace.json`.

## Adding Plugins

To add a plugin to this marketplace:

1. Create your plugin in the `plugins/` directory
2. Add an entry to `.claude-plugin/marketplace.json`:

```json
{
  "name": "your-plugin-name",
  "source": "./plugins/your-plugin-name",
  "description": "Brief description of your plugin",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "your-email@example.com"
  },
  "license": "MIT",
  "keywords": ["tag1", "tag2"]
}
```

3. Validate your marketplace:

```bash
/plugin validate .
```

## Plugin Structure

Each plugin should have this structure:

```
plugins/your-plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── your-command.md
└── README.md
```

## Updating

Users can update all plugins from this marketplace with:

```bash
/plugin marketplace update
```

## License

MIT
