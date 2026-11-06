# dbd

Simple database deployment tool.

## Running dbd

The command-line syntax is:

```text
dbd install <configuration-file> [--name=value ...]
```

Command-line values are available from the `CLI` expander. The `help` action
prints the help entry point:

```text
dbd --help
```

## Configuration file

The configuration file is JSON. It contains a driver configuration and one
configuration block for each runtime component:

```json
{
  "driver": {
    "mappings": {
      "ENVIRONMENT": "development"
    }
  },
  "secret_reader": {
    "type": "file",
    "config": {
      "file_name": "secrets.json",
      "type": "json"
    }
  },
  "record_keeper": {
    "type": "postgres",
    "config": {
      "connection": {
        "host": "localhost",
        "port": 5432,
        "dbname": "application",
        "user": "dbd",
        "password": "__SECRET(database-password)",
        "sslmode": "prefer"
      }
    }
  },
  "source_provider": {
    "type": "file",
    "config": {
      "path": "sql",
      "file_masks": ["*.sql", "*.ddl"]
    }
  },
  "destination_system": {
    "type": "postgres",
    "config": {
      "connection": {
        "host": "localhost",
        "port": 5432,
        "dbname": "application",
        "user": "dbd",
        "password": "__SECRET(database-password)",
        "sslmode": "prefer"
      }
    }
  }
}
```

Each component has the following structure:

| Property | Required | Description |
|----------|----------|-------------|
| `type` | yes | Name of the implementation subdirectory under `dbd.implementations`. |
| `config` | yes | Implementation-specific settings passed to the class constructor. |
| `source_file_override` | no | Python module name; defaults to the component module name. |
| `class_override` | no | Class name; defaults to `SecretReader`, `RecordKeeper`, `SourceProvider`, or `DestinationSystem`, depending on the component. |

### Dynamic component loading

Components are loaded at runtime using this convention:

```text
dbd.implementations.<type>.<source_file>
```

The default module names are:

| Component | Default module | Default class |
|-----------|----------------|---------------|
| Secret reader | `secret_reader` | `SecretReader` |
| Record keeper | `record_keeper` | `RecordKeeper` |
| Source provider | `source_provider` | `SourceProvider` |
| Destination system | `destination_system` | `DestinationSystem` |

For example, this configuration:

```json
{
  "record_keeper": {
    "type": "postgres",
    "config": {}
  }
}
```

loads `dbd.implementations.postgres.record_keeper.RecordKeeper` and
constructs it with the nested `config` object. Overrides are useful when an
implementation uses a different module or class name:

```json
{
  "record_keeper": {
    "type": "custom",
    "source_file_override": "audit_keeper",
    "class_override": "AuditRecordKeeper",
    "config": {}
  }
}
```

The resulting class must implement the interface expected by its component
role. The loader uses dynamic imports, so invalid type, module, or class names
are reported when the configuration is loaded.

The secret-reader configuration is expanded in two stages. The component
selection is read first so the secret reader can be instantiated; the reader
is then passed to the configuration expander so `SECRET` placeholders in the
other component configurations can be resolved. Consequently, a `SECRET`
placeholder cannot be used to select or configure the secret reader itself.

### JSON Schemas

The root schema is
[`documentation/schemas/dbd.schema.json`](documentation/schemas/dbd.schema.json).
Implementation-specific schemas are stored below the component type
directories, for example:

- [`documentation/schemas/postgres/record_keeper.schema.json`](documentation/schemas/postgres/record_keeper.schema.json)
- [`documentation/schemas/postgres/destination_system.schema.json`](documentation/schemas/postgres/destination_system.schema.json)
- [`documentation/schemas/file/source_provider.schema.json`](documentation/schemas/file/source_provider.schema.json)
- [`documentation/schemas/file/secret_reader.schema.json`](documentation/schemas/file/secret_reader.schema.json)

The root schema uses JSON Schema `$ref` for fixed schema relationships such as
the driver configuration. Relative references are resolved from the schema
file containing the `$ref`; therefore `./driver.schema.json` refers to
`documentation/schemas/driver.schema.json`. Since the implementation schema
depends on the configured `type`, tools should validate the corresponding
implementation schema for the selected component.

### Expander placeholders

Expander placeholders represent simple built-in functions that allow easy modularization of the configuration file. They 
take one input argument.

The syntax of the placeholders is as follows:

```
__<PLACEHOLDER>(<PARAMETER>)
```

Following placeholders are available:

| Placeholder | Parameter                                     | Description                                                      |
|-------------|-----------------------------------------------|------------------------------------------------------------------|
| `CFG`       | The configuration key                         | References other value within this configuration                 |
| `CLI`       | The command-line parameter name               | Returns the value of the command line parameter passed in        |
| `ENV`       | The OS environment variable name, e.g. `PATH` | Returns the value of the specified environment variable.         |
| `FILE`      | The file path, e.g. `/tmp/myfile.txt`         | Returns the content of the specified file.                       |
| `SECRET`    | The secret name, e.g. `my-secret`             | Returns the value of the specified secret from the secret store. |
