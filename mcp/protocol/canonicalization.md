# Verity Canonicalization Specification

## 1. Introduction

- Purpose of deterministic canonicalization

## 2. Design Goals

- Deterministic

- Domain agnostic

- Versioned

- Language independent

## 3. Canonicalization Workflow

- Structured assertions
- Deterministic normalization
- Canonical graph representation
  
## 4. Source Canonicalization

- Source identifiers

- Normalization rules

### 4.1 Source Identifiers

A source refers to the origin of one or more claims.

Clients MUST define the source type prior to invoking the Verity SDK. The SDK MUST NOT infer the source identity based on the source identifier provided.

Types of sources that are supported include:

- `web_publisher`
- `web_document`
- `internal_resource`
- `internal_service`
- `database`
- `package`

### 4.2 Normalization Rules

For `web_publisher` sources, the SDK MUST:

- Make the domain name lowercase.
- Strip a trailing DNS dot from the domain name.
- Transform internationalized domain names through IDNA.
- Fail for identifiers containing path, query, or fragment information.

For `web_document` sources, the SDK MUST:

- Make the URI scheme and host lowercase.
- Strip default ports.
- Strip URI fragments.
- Keep paths and query parameters intact.
- Normalize the URI according to RFC 3986.

For all source types, the SDK MUST reject ambiguous identifiers that cannot be deterministically normalized.

### 4.3 Examples

For example:

Input

```text
https://docs.anthropic.com/
```

Canonical

```text
docs.anthropic.com
```

---

Input

```text
HTTPS://Example.com:443/docs/api#section
```

Canonical

```text
https://example.com/docs/api
```

---

Input

```text
Confluence:Page:184920
```

Canonical

```text
confluence:page:184920
```

---

Input

```text
the documentation
```

Result

```text
Rejected
```

Reason

```text
Source identifier is ambiguous.
```

## 5. Claim Canonicalization

### 5.1 Entity

### 5.2 Attribute

### 5.3 Value

### 5.4 Units

### 5.5 Examples

## 6. Assertion Construction

### 6.1 Source

### 6.2 Claim

### 6.3 Assertion

### 6.4 Examples

## 7. Canonical Forms

### 7.1 Canonical Source

### 7.2 Canonical Claim

### 7.3 Canonical Assertion

## 8. Versioning

- Canonicalization specification versions

## 9. Conformance

- Requirements for compliant implementations
