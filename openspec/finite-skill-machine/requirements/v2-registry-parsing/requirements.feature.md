# Feature: V2 Registry Parsing (v2-registry-parsing)

<!--
DO NOT REMOVE THIS HEADER - it documents terminology mapping for editors.

MDG format. Invoke skill: tokamak:writing-markdown-gherkin for full reference.

TERMINOLOGY (proposal language → Gherkin keyword):
- "Capability" → "Feature" (one Feature per capability)
- "Requirement" → "Rule" (requirements are grouped as Rules)

We use Gherkin syntax, so headers say "Feature" and "Rule".
-->

## Requirements

`@v2-registry-parsing:1`
### Rule: The hook SHALL detect the registry format from the root JSON structure

The hook SHALL distinguish v1 (root is array) from v2 (root is object with integer `version` field) by inspecting the parsed JSON type and version value. Unrecognised structures SHALL cause the hook to fail-closed with an actionable error message.

#### Background
- Given installed_plugins.json exists and contains valid JSON

`@v2-registry-parsing:1.1`
#### Scenario: Object with version 2 detected as v2 format

- Given installed_plugins.json contains `{"version": 2, "plugins": {}}`
- When the hook reads installed_plugins.json
- Then the hook treats the file as v2 format

`@v2-registry-parsing:1.2`
#### Scenario: Array at root detected as v1 format

- Given installed_plugins.json contains `[{"name": "plugin@1.0.0"}]`
- When the hook reads installed_plugins.json
- Then the hook treats the file as v1 format

`@v2-registry-parsing:1.3`
#### Scenario: Object without version field treated as malformed

- Given installed_plugins.json contains `{"plugins": {}}`
- When the hook reads installed_plugins.json
- Then the hook exits with a non-zero exit code
- And the error message indicates the file is malformed

`@v2-registry-parsing:1.4`
#### Scenario: Unknown version number treated as unsupported

- Given installed_plugins.json contains `{"version": 3, "plugins": {}}`
- When the hook reads installed_plugins.json
- Then the hook exits with a non-zero exit code
- And the error message indicates the version is unsupported

`@v2-registry-parsing:2`
### Rule: The hook SHALL match plugins by key in the v2 plugins object

The hook SHALL extract the plugin name from commandName (portion before `:`) and match it against keys in the v2 `plugins` object, where keys use `plugin@marketplace` format. Matching SHALL compare the plugin name against the portion of each key before `@`.

`@v2-registry-parsing:2.1`
#### Scenario: Plugin key matched by name portion of commandName

- Given installed_plugins.json is v2 format
- And the plugins object contains key "my-plugin@chaos-theory"
- When the hook resolves commandName "my-plugin:my-skill"
- Then the hook selects the entries under "my-plugin@chaos-theory"

`@v2-registry-parsing:2.2`
#### Scenario: No matching plugin key falls through to non-plugin lookup

- Given installed_plugins.json is v2 format
- And the plugins object contains no key matching "my-plugin"
- When the hook resolves commandName "my-plugin:my-skill"
- Then the hook falls back to non-plugin skill resolution

`@v2-registry-parsing:2.3`
#### Scenario: Empty plugins object falls through to non-plugin lookup

- Given installed_plugins.json is v2 format
- And the plugins object is empty
- When the hook resolves commandName "my-plugin:my-skill"
- Then the hook falls back to non-plugin skill resolution

`@v2-registry-parsing:2.4`
#### Scenario: Multiple plugin keys, only matching key used

- Given installed_plugins.json is v2 format
- And the plugins object contains keys "alpha@marketplace" and "beta@marketplace"
- When the hook resolves commandName "beta:my-skill"
- Then the hook selects the entries under "beta@marketplace"
- And the entries under "alpha@marketplace" are not considered

`@v2-registry-parsing:3`
### Rule: The hook SHALL apply scope precedence over v2 entry arrays

The hook SHALL iterate installation entries within the matched plugin key's array, applying scope precedence (local > project > user) and projectPath matching against cwd. This is the same precedence logic as v1, applied over the v2 data structure.

`@v2-registry-parsing:3.1`
#### Scenario Outline: Scope precedence within v2 entry array

- Given the matched plugin key has entries with <higher> and <lower> scopes
- And cwd matches both entries' projectPath
- When the hook selects an installation entry
- Then it uses the <higher> scope entry

##### Examples
| higher  | lower   |
|---------|---------|
| local   | project |
| local   | user    |
| project | user    |

`@v2-registry-parsing:3.2`
#### Scenario: Single entry in array used directly

- Given the matched plugin key has one entry with scope "project"
- And cwd matches the entry's projectPath
- When the hook selects an installation entry
- Then it uses that entry's installPath

`@v2-registry-parsing:3.3`
#### Scenario: projectPath matching filters v2 entries

- Given the matched plugin key has an entry with scope "project" and projectPath "/projects/myapp"
- And cwd is "/projects/myapp/src/components"
- When the hook selects an installation entry
- Then the entry is considered a match (cwd is under projectPath)

`@v2-registry-parsing:3.4`
#### Scenario: projectPath non-matching excludes entry

- Given the matched plugin key has an entry with scope "project" and projectPath "/projects/myapp"
- And cwd is "/projects/otherapp"
- When the hook selects an installation entry
- Then the entry is not used

`@v2-registry-parsing:3.5`
#### Scenario: Entry without installPath skipped

- Given the matched plugin key has an entry that lacks an installPath field
- When the hook selects an installation entry
- Then that entry is skipped
- And the hook continues to the next entry

`@v2-registry-parsing:4`
### Rule: The hook SHALL fail closed for malformed v2 registry structures

The hook SHALL fail-closed when the v2 registry structure is internally invalid, and SHALL fall back to non-plugin lookup when the plugin is simply absent from a valid registry.

`@v2-registry-parsing:4.1`
#### Scenario: Plugin not in v2 registry falls back to non-plugin lookup

- Given installed_plugins.json is valid v2 format
- And the plugins object has no key matching the plugin name
- When the hook resolves a plugin skill commandName
- Then the hook falls back to non-plugin skill resolution

`@v2-registry-parsing:4.2`
#### Scenario: Malformed JSON in registry file fails the hook

- Given installed_plugins.json contains invalid JSON
- When the hook reads installed_plugins.json
- Then the hook exits with a non-zero exit code
- And the error message describes the parse failure

`@v2-registry-parsing:4.3`
#### Scenario: plugins field is not an object fails the hook

- Given installed_plugins.json contains `{"version": 2, "plugins": []}`
- When the hook reads installed_plugins.json
- Then the hook exits with a non-zero exit code
- And the error message indicates invalid registry structure

`@v2-registry-parsing:4.4`
#### Scenario: Missing plugins key in v2 object fails the hook

- Given installed_plugins.json contains `{"version": 2}`
- When the hook reads installed_plugins.json
- Then the hook exits with a non-zero exit code
- And the error message indicates missing plugins field
