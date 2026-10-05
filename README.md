# dbd
Simple (database) deployment tool

## Configuration file

### Expander placeholders

Expander placeholders represent simple built-in functions that allow easy modularization of the configuration file. They 
take one input argument. following placeholders are available:

| Placeholder | Parameter                                     | Description                                                      |
|-------------|-----------------------------------------------|------------------------------------------------------------------|
| `CLI`       | The command-line parameter name               | Returns the value of the command line parameter passed in        |
| `ENV`       | The OS environment variable name, e.g. `PATH` | Returns the value of the specified environment variable.         |
| `FILE`      | The file path, e.g. `/tmp/myfile.txt`         | Returns the content of the specified file.                       |
| `SECRET`    | The secret name, e.g. `my-secret`             | Returns the value of the specified secret from the secret store. |
