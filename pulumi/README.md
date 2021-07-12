# Lightlytics Pulumi

## Prerequisites

- Python 3.7-3.9 - https://realpython.com/installing-python/
- Pulumi CLI - https://www.pulumi.com/docs/get-started/install/

## Style Guides ##

- Python: we are using the [google](https://google.github.io/styleguide/pyguide.html) style guide
  with [yapf](https://github.com/google/yapf/), your code will not pass test if it's not properly formatted.  
  To run yapf in each repo, use: `yapf --recursive -p . --diff` or `make fmt`

## Git Guideline ##

- Use `git merge` **NOT** `rabase`

## Pulumi Base Structure ##

`Pulumi.yaml` - defines the project.  
`Pulumi.<stack_name>.yaml` - contains configuration values for the stack you initialized.  
`__main__.py` - is the Pulumi program that defines your stack resources

- **Init** - `pulumi new`
- **Login** - `pulumi login`
- **Deploy** - `pulumi up`  
  When you run the pulumi up command, Pulumi will compute this desired state, compare it to the current infrastructure
  you already have (if any), show you the delta, and let you confirm and carry out the changes.
- **Destroy** - `pulumi destroy`  
  To delete the stack itself, run `pulumi stack rm`. Note that this removes the stack entirely from the Pulumi Service,
  along with all of its update history.

All [output][output-url] data (everything with `pulumi.export`) can be accessed using:
`pulumi stack output <name of the output>`

## Pulumi Concepts ##

- **Program**: a collection of files written in your chosen programming language. A program becomes a project by virtue
  of a Pulumi.yaml manifest that describes it in the root directory
- **Project**: a directory containing a program, with metadata, so Pulumi knows how to run it
- **Stack**: an instance of your project, each often corresponding to a different cloud environment.  
  Every Pulumi program is deployed to a stack. A stack is an isolated, independently configurable instance of a Pulumi
  program. Stacks are commonly used to denote different phases of development (such as development, staging and
  production) or feature branches (such as feature-x-dev, jane-feature-x-dev).
- **Pulumi SDK** - The [Pulumi SDK](https://www.pulumi.com/docs/intro/concepts/programming-model/#pulumipulumi) library
  defines Pulumi’s most fundamental types and functions
- **State**: Pulumi stores its own copy of the current state of your infrastructure. This is often simply called `state`
  , and is stored in transactional snapshots we call `checkpoints`. A `checkpoint` is recorded by Pulumi at various
  points so that it can operate reliably—whether that means diffing goal state versus current state during an update,
  recovering from failure, or destroying resources accurately to clean up afterwards.
- **Backends**
  Pulumi supports multiple backends for storing your infrastructure state:
- [The Pulumi Service backend](https://www.pulumi.com/docs/intro/concepts/state/#pulumi-service-backend)
- [A self-managed backend, either stored locally on your filesystem or remotely using a cloud storage service](https://www.pulumi.com/docs/intro/concepts/state/#self-managed-backends)

## Usage ##

- Switch AWS
  profile: `pulumi config set aws:profile <profilename>` [More aws config](https://www.pulumi.com/docs/intro/cloud-providers/aws/#configuration)
- Check login info: `pulumi whoami -v`

### Stack Usage:

- Create Stack: `pulumi stack init stackName` or create stack in our org: `pulumi stack init lightlytics/staging`  
  Note that while stacks with applied configuration settings will often be accompanied by Pulumi.<stack-name>.yaml
  files,  
  these files are not created by `pulumi stack init`. They are created and managed with `pulumi config`.
- List Stacks: `pulumi stack ls`
- Select Stack: `pulumi stack select <stack-name>` OR `pulumi stack init lightlytics/staging`
- View stack resource: `pulumi stack`
- View stack outputs: `pulumi stack output` or `pulumi stack output <export(output)-name>`
- Import and export a stack deployment: `pulumi stack export --file stack.json / pulumi stack import --file stack.json`
- Stack tags - `pulumi stack tag ls`
- Custom tags - `pulumi stack tag set <name> <value>`
- Delete Tags - `pulumi stack tag rm <name>`

### Exports

- Exporting values; You can export resulting infrastructure values that you wish to access outside your application.   
  For example, export the server’s resulting IP address and DNS name:

```python
# ...
pulumi.export('public_ip', server.public_ip)
pulumi.export('public_dns', server.public_dns)
```

The exported values are printed after you do a `pulumi up` and they are easy to access from the
CLI’s `pulumi stack output` command.

### Configuration and Secrets

#### Config

Configuration allows you to parameterize your program based on externally managed configuration. This can be helpful if
you want to, say, have a different number of servers in your production stack than in development. Configuration keys
use the format `<namespace>:<key-name>`, with a colon delimiting the optional namespace and the actual key name. In
cases where a simple name without a colon is used, Pulumi automatically uses the current project name from Pulumi.yaml
as the namespace.

- https://www.pulumi.com/docs/intro/concepts/config/#config-stack

- Cli Access:
- The key-value pairs for any given stack are stored in your project’s stack settings file, which is automatically named
  Pulumi.<stack-name>.yaml.
- The CLI offers a config command with `set` and `get` subcommands for managing key-value pairs.
- The programming model offers a `Config` object with various getters and setters for retrieving values.
- `pulumi config set <key> [value]` sets a configuration entry `<key>` to `[value]`.
  Example: `pulumi config set aws:region us-west-2`
- `pulumi config get <key>` gets an existing configuration value with the key `<key>`.
  Example: `pulumi config get aws:region` / `cat my_key.pub | pulumi config set publicKey`
- `pulumi config` gets all configuration key-value pairs in the current stack (as JSON if --json is passed).
  > Note: When using the config set command, any existing values for <key> will be overridden without warning.
- Structured Configuration:

```shell
pulumi config set --path 'data.active' true 
pulumi config set --path 'data.nums[0]' 1
# Secrets:
pulumi config set --path endpoints[0].url https://example.com
pulumi config set --path --secret endpoints[0].token accesstokenvalue
``` 

The structure of data is persisted in the stack’s Pulumi.<stack-name>.yaml file as:

```yaml
config:
  proj:data:
    active: true
    nums:
      - 1
```

- Code Access:
- https://www.pulumi.com/docs/reference/pkg/python/pulumi/
  Example:

```python
import pulumi

# After running `pulumi config set myconfig 42` 
config = pulumi.Config("optional project name space here if not set then it will use current");
print(config.get_int("myconfig"))  # prints 42
# For secrets (below)
# this will not print, will say that it is encrypted.
print(config.require_secret('dbPassword'))

# Structured conf from above example:
config = pulumi.Config()
data = config.require_object("data")
print("Active:", data.get("active"))

```

#### Secrets

The Pulumi Service transmits and stores entire state files securely, however, Pulumi also supports encrypting specific
values as “secrets” beyond this for extra protection. This ensures that these values never appear as plaintext in your
state. The encryption uses automatic per-stack encryption keys provided by the Pulumi Service by default, or you can use
a provider of your own choosing.

- Cli Access:
- `pulumi config set --secret <secret name> <value>`, Example: `pulumi config set --secret dbPassword S3cr37`
- View secrets and conf: `pulumi config`

> **WARNING: On pulumi up, secret values are decrypted and made available in plaintext at runtime.
> These may be read through any of the standard `pulumi.Config` getters shown above.
> While it is possible to read a secret using the ordinary non-secret getters, this is almost certainly not
> what you want. Use the secret variants of the configuration APIs instead,
> since this ensures that all transitive uses of that secret are themselves also marked as secrets.**

- Configuring Secrets Encryption
- https://www.pulumi.com/docs/intro/concepts/config/#configuring-secrets-encryption
- **The Pulumi Service automatically manages per-stack encryption keys on your behalf**
- The default encryption mechanism may be insufficient in the following scenarios:
- If you are using the Pulumi CLI independent of the Pulumi Service—either in local mode, or by using one of the
  available backend plugins (such as those that store state in AWS S3, Azure Blob Store, or Google Object Storage).
- If your team already has a preferred cloud encryption provider that you would like to use.

In both cases, you can continue using secrets management as described above, but instruct Pulumi to use an alternative
encryption provider.

- To Use [KMS][KMS-URL] instead of pulumi service

#### Backends and secrets

When a secret value is provided via secret configuration — either by passing `--secret` to `pulumi config set` or by
creating one inside your program via `Output.secret` (Python), **the value is encrypted with a key managed by the
backend you are connected to. When using the local or remote backend, this key is derived from a passphrase you set when
creating your stack. When using the Pulumi Service backend, it is handled by a key managed by the service.**
**When using the filesystem or cloud storage backend, you must use the passphrase-based secrets provider.**

## Outputs and Inputs
- https://www.pulumi.com/docs/reference/pkg/python/pulumi/#outputs-and-inputs
Like other languages in the Pulumi ecosystem, all Resources in Python have two kinds of properties: `inputs`
and `outputs`.
`Inputs` are specified as arguments to `resource` constructors, to be used as inputs to the resource itself. `Outputs`
are
`returned` as properties on the instantiated resource object. `Outputs` are similar to `futures` in that they are
resolved asynchronously, but they also contain information about the dependency graph of resources within your program.

- Output helps encode the relationship between Resources in a Pulumi application. Specifically an Output holds onto a
  piece of Data, and the Resource it was generated from. An Output value can then be provided when constructing new
  Resources, allowing that new Resource to know both the value, and the Resource the value came from. This allows for a
  precise ‘Resource dependency graph’ to be created, which properly tracks the relationship between resources.

## Resources & Providers

### Resources:

All infrastructure resources are described by subclasses of the `Resource` class. A class that derives
from `pulumi.Resource` will, *when instantiated*, communicate with the Pulumi Engine and record that a piece of
infrastructure that the instantiated class represents should be provisioned.

- `Resource` represents a class whose CRUD operations are implemented by
  a [provider plugin](https://www.pulumi.com/docs/intro/cloud-providers/) (
  such as AWS).

**Important:**

- All classes that can be instantiated to produce actual resources derive from the `pulumi.Resource class`.
- All resources whose provisioning is implemented in a `resource provider` derive from the `pulumi.CustomResource`
  class.
- Resources written in `Python` are called `component resources`, and they are written by deriving from
  the `pulumi.ComponentResource` class.**
- Pulumi allows for `resource providers` to directly project themselves into Python, so that provider instances can be
  instantiated and used to create other resources. These `provider resources` derive from the pulumi.ProviderResource
  class.
  https://www.pulumi.com/docs/intro/concepts/programming-model/#explicit-provider-configuration

So to wrap up - there are two families of resources that branch from this base class:

- `CustomResource` external resources managed by a `resource provider` (such as `pulumi-resource-aws`, most common)
  CustomResource is a resource whose create, read, update, and delete (CRUD) operations are managed by performing
  external operations on some physical entity. The engine understands how to diff and perform partial updates of them,
  and these CRUD operations are implemented in a dynamically loaded plugin for the defining package.
- `ComponentResource` an aggregation of many resources to form a larger abstraction. ComponentResource is a resource
  that aggregates one or more other child resources into a higher level abstraction. The component itself is a resource,
  but does not require custom CRUD operations for provisioning.
- `ProviderResource` is a resource that implements CRUD operations for other custom resources. These resources are
  managed similarly to other resources, including the usual diffing and update semantics.

### Providers:

- The resource provider for a custom resource is determined based on its package name. For example, the aws package will
  load a plugin named `pulumi-resource-aws`, and the kubernetes package will load a plugin named
  `pulumi-resource-kubernetes`. Each provider uses the configuration from its package to alter its behavior.

- Resource Providers Plugins:
  Any packages that create custom resources—classes that derive from the `CustomResource` base class, will cause Pulumi
  to load an associated `resource provider plugin` at runtime, which is a binary that implements the Create, Read,
  Update, and Delete resources defined by the package. Normally plugins are installed automatically when you install the
  package, but you can also manage plugins explicitly using the CLI.

- This is in contrast to a component resource—classes that derive from the `ComponentResource` base class whose logic is
  written entirely within that library itself, without any external plugin required. A component resource does not
  manage any external infrastructure state; instead, it simply aggregates existing resources into a larger abstraction.
  For Example: https://www.pulumi.com/docs/tutorials/aws/s3-folder-component/

- Finally, `dynamic providers` let you write an entire provider within your language of choice, without needing to
  create a resource provider plugin. This has the advantage that you can flexibly create new resource types—but with the
  disadvantage that you can’t share them easily across multiple languages, as resource plugins are language-neutral.
  https://www.pulumi.com/docs/intro/concepts/programming-model/#how-dynamic-providers-work

[output-url]: https://www.pulumi.com/docs/intro/concepts/stack/#outputs

[KMS-URL]: https://www.pulumi.com/docs/intro/concepts/config/#aws-key-management-service-kms