# Gateway Service

Kong API Gateway configuration for the monorepo services.

## Configuration

The gateway is configured using Kong's declarative configuration format in `kong.yml`.

### Format Version

This configuration uses Kong's declarative format version 3.0 with transform enabled.

### Structure

- **Services**: Backend services that Kong will proxy to
- **Routes**: Request routing rules to match incoming requests to services
- **Plugins**: Kong plugins for authentication, rate limiting, etc.
- **Upstreams**: Load balancing configuration for multiple service instances
- **Consumers**: API consumers for authentication and rate limiting

## Usage

The configuration file can be used with Kong in declarative mode:

```bash
kong start -c kong.conf --declarative-config kong.yml
```

## Validation

Validate the configuration using yamllint:

```bash
yamllint apps/gateway/kong.yml
```
