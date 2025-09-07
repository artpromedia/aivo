# API Documentation

This directory contains all API contracts and specifications for the monorepo.

## Structure

```text
docs/api/
├── README.md                    # This file
├── rest/                        # REST API specifications
│   ├── .spectral.yaml          # Spectral linting rules
│   └── _examples/              # Sample API specifications
│       └── ping.yaml           # Health check API example
└── graphql/                     # GraphQL API specifications
    └── schema.graphql          # Main GraphQL schema
```

## REST APIs

### OpenAPI Specifications

All REST APIs should follow the OpenAPI 3.1 specification format. Place your
API specs in the appropriate service directory under `docs/api/rest/`.

### Spectral Linting

We use [Spectral](https://stoplight.io/open-source/spectral) for API contract
linting. The rules are defined in `.spectral.yaml`:

- **tags-required**: All operations must have tags
- **contact-required**: API must have contact information
- **servers-non-empty**: API must define at least one server
- **operation-summary**: Operations should have summaries
- **operation-description**: Operations should have descriptions
- **schema-examples**: Schema properties should have examples
- **response-examples**: Responses should have examples

### Validation

Run the contract linter:

```bash
pnpm run contracts:lint
```

## GraphQL APIs

### Schema Definition

GraphQL schemas should be defined using the GraphQL Schema Definition Language
(SDL). Place your schema files in `docs/api/graphql/`.

### Best Practices

- Use descriptive names for types, fields, and operations
- Provide documentation strings for all public types and fields
- Define custom scalars for complex types (DateTime, JSON, etc.)
- Use interfaces and unions appropriately
- Implement proper error handling

## Development Workflow

### Adding a New API

1. **Choose the API style**: REST or GraphQL
2. **Create the specification**:
   - For REST: Create an OpenAPI YAML file
   - For GraphQL: Add to the schema.graphql file
3. **Add examples**: Include request/response examples
4. **Document**: Update this README if needed
5. **Validate**: Run `pnpm run contracts:lint`
6. **Commit**: Use conventional commit format

### API Design Principles

- **Contract-first**: Design APIs before implementation
- **Versioning**: Use URL versioning for REST APIs
- **Consistency**: Follow consistent naming conventions
- **Documentation**: Keep API specs up to date
- **Validation**: Use the provided linting rules

## Tools

- **Spectral**: API contract linting
- **OpenAPI 3.1**: REST API specification format
- **GraphQL SDL**: Schema definition language

## Examples

See `docs/api/rest/_examples/ping.yaml` for a complete OpenAPI specification
example.

## Contact

For questions about API design or specifications, contact the API team.
