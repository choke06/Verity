# Source Dependencies

If two sources agree, it does not necessarily mean that they are independent.

The same claim may be asserted by two independent sources because they both independently arrived at the same information.

Alternatively, the same claim may be asserted by two dependent sources based on one copying the other.

From the perspective of a credibility propagation algorithm, these two instances appear identical despite the different evidence.

As a consequence, a large number of dependent sources can create an illusion of high consensus despite a lack of independent evidence. In contrast, a small number of independent sources can be worth more than a large number of sources with copied information.

## Research Question

Is there a way to determine source dependencies based exclusively on the source-claim graph?

## Hypothesis

Let's suppose Source B depends on Source A.

In that case, the information asserted by Source B should typically be explained better by the information asserted by Source A more than vice versa.

This directional asymmetry of the relationship could, perhaps, be used to infer the dependency that does not require introducing explicit citation or metadata.

## Current Research Questions

- How is this best modeled mathematically / what concept fits best?
- Is there a way or method to figure out the dependencies purely based on graph structure?
- How do we incorporate inferred dependencies into credibility propagation?
- How do we model partial dependencies?
- How do we handle common upstream source?