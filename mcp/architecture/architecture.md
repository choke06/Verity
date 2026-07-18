# Verity Architecture

## 1. Objectives

This document provides a high-level overview and defines fundamental architectural components and their interactions that make up the Verity architecture.

The architecture is designed to compute structural credibility over structured assertions collected from various independent sources.

A major goal for Verity is to enable integration with existing structured data pipelines, regardless of application domain, programming language, or deployment environment used.

Here is a brief summary of the design principles:

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

Applications can install and integrate the Verity SDK directly into their existing structured data pipelines. The SDK performs deterministic canonicalization, constructs a credibility graph, generates privacy-preserving linkage tokens, and submits graph updates to a Verity deployment.

A Verity deployment persists a credibility graph as new assertions are received. The deployment is responsible for executing structural credibility inference and returning credibility signals to an application. The credibility graph may be private to a single organization or shared across multiple participants (depending on the deployment model used).

<p align="center">
  <img src="diagrams/system_architecture.png" alt="Verity system architecture" width="600">
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
- Existing pipeline
- Structured output
- Verity SDK
- Canonicalization
- OPRF
- Verity deployment
- Inference engine
- Credibility response
  
## 5. Graph Workflow
- Graph construction
- Graph evolution
- Snapshotting
- Recomputation

## 6. Deployment Options
- Self-hosting
- Cloud-based deployment

## 7. Trust Boundary
- Data crossing the trust boundary.
- Data that is not exposed to Verity.

## 8. Persistent Storage Model
- Graph storage
- Identifiers
- Linkage tokens
- Snapshots

## 9. Inference Workflow
- Graph updates
- Background recomputation
- Propagation
- Convergence
- Score publication

## 10. Failure Recovery

- Crash recovery
- Partial writes
- Idempotency
- Graph consistency

## 11. Scalability

- Incremental computation
- Parallel inference
- Horizontal scaling
