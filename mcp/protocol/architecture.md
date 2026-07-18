# Verity Architecture

This document provides a high-level overview and defines fundamental architectural components and their interactions that make up the Verity architecture.

To see specification details, visit:

- **protocol.md** — the communication contract between clients and Verity deployments. Defines the JSON-RPC protocol and request & response formats.
- **canonicalization.md** — deterministic normalization rules. Specifies how semantically equivalent assertions produce the same graph representation before inference.
- **sdk.md** — client integration guides for constructing graphs, linkage token generation, submitting requests from supported languages.
- **mcp.md** — reference documentation for the methods exposed by Verity deployments. Includes request schemas, parameters, response structures.

## 1. Objectives

The system architecture is designed to compute structural credibility over structured assertions collected from various independent sources.

A major goal for Verity is to enable integration with existing structured data pipelines, regardless of application domain, programming language, or deployment environment used.

Here is a brief summary of the notable design principles:

- Semantic extraction is separated from credibility inference.
- Deterministic graph construction through standardized canonicalization.
- Privacy-preserving linkage using tokens instead of the underlying content of the data.
- Support for both self-hosted and cloud-based deployments.
- A persistent credibility graph that evolves with the addition of new assertions.
- Producing deterministic credibility signals from graph topology.
- Scaling to large, continuously evolving credibility networks.
  
## 2. System Overview

At the highest level, Verity is composed of three key architectural components:

- Verity SDK
- Verity Deployment
- Inference Engine

Applications can install and integrate the Verity SDK directly into their structured data pipelines. The SDK performs deterministic canonicalization, constructs a credibility graph, generates privacy-preserving linkage tokens, and submits graph updates to a Verity deployment.

A Verity deployment persists a credibility graph as new assertions are received. The deployment is responsible for executing structural credibility inference and returning credibility signals to an application. The credibility graph may be private to a single organization or shared across multiple participants (depending on the deployment model used).

<p align="center">
  <img src="../diagrams/architecture.png" alt="Verity system architecture" width="600">
</p>

<p align="center">
  <em>Figure 1. High-level architecture of the Verity system.</em>
</p>

## 3. Architectural Components

### 3.1 Verity SDK

The Verity SDK exposes the Verity API for application use. The SDK serves as the primary integration point between applications and a Verity deployment.

### 3.2 Verity Deployment

A Verity deployment receives graph updates from the Verity SDK and manages the overall execution of the inference engine. A deployment is the runtime environment for the Verity system.

### 3.3 Inference Engine

The inference engine in Verity implements an iterative graph-based propagation ranking method. It computes structural credibility scores by propagating credibility throughout the graph.

## 4. End-to-End Workflow

This section specifies how data flows through a Verity deployment, from the point an application creates structured assertions to receiving credibility signals.

### 4.1 Structured Data Pipeline

A core principle of Verity is it does not analyze raw data. Applications collect and organize information from their own data sources. Some examples of data sources could include REST APIs, databases such as SQL, documents, spreadsheets, knowledge bases, MCP tools, or even the outputs of AI agents. The application should intrepret the data and convert it to structured assertions before interacting with Verity.

The method used to perform semantic extraction is outside the scope of Verity.

### 4.2 Canonicalization

The Verity SDK applies deterministic canonicalization to structured assertions before constructing graph updates. The canonicalization rules are defined in the Verity Canonicalization Specification.

### 4.3 Linkage Token Generation

The SDK generates privacy-preserving linkage tokens from the canonicalized graph update. The linkage protocol is defined separately from the system architecture.

### 4.4 Graph Update Construction

The SDK constructs a graph update message containing the linkage tokens and associated protocol metadata before submitting it to a Verity deployment.

### 4.5 Graph Submission

The graph update is transmitted to a Verity deployment using a supported protocol binding (such as MCP).

### 4.6 Credibility Inference

After submission, the deployment resolves the linkage tokens and updates the persistent credibiliy graph, then executes the configured inference algorithm to compute structural credibility.

### 4.7 Credibility Response

The deployment returns deterministic credibility signals to the application.

## 5. Credibility Graph

Each Verity deployment maintains a persistent data structure which is referred to as a credibility graph. The credibility graph models how sources and claims connect through assertions, enabling structural credibility to be computed over the graph topology.

### 5.1 Graph Structure

The credibility graph is modeled as a bipartite graph where source and claim nodes connect through their assertions (edges). When an application submits a graph update, it contributes additional topology to the graph.

### 5.2 Graph Evolution

As new graph updates are received, the credibility graph evolves. Verity does not reconstruct the graph on every request; it incrementally expands the existing graph with additional assertions.

### 5.3 Persistence

A Verity deployment maintains the credibility graph across requests. This persistent graph allows credibility to accumulate over time as more independent assertions are contributed by participating applications.

### 5.4 Snapshots

Credibility inference is performed over a consistent snapshot of the credibility graph. This allows graph updates and credibility computation to operate independently while ensuring deterministic inference for a given graph state.

## 6. Deployment

### 6.1 Deployment Models

Verity deployments may be self-hosted or cloud-hosted. Every deployment implements the same protocol and maintains a persistent credibility graph regardless of deployment model. The deployment model mainly affects where the credibility graph is stored and administered, but does not alter the behavior defined by the Verity Protocol.

### 6.2 Trust Boundary

Applications must perform semantic extraction and canonicalization before interacting with Verity. Verity operates only on protocol-compliant graph updates and does not interpret the underlying content. This separation establishes the trust boundary between application-specific processing and structural credibility inference.
