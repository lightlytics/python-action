# Datadog Agent #

## Install

- To Install run:
```bash
helm install datadog -f datadog-values.yaml -n datadog --create-namespace stable/datadog
```

## Update Agent

- To Update run:

```bash
helm upgrade -f datadog-values.yaml -n datadog datadog stable/datadog

```

