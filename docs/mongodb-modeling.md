# MongoDB data modeling: embed or reference?

The core decision in MongoDB schema design is whether related data lives
inside the same document (embedding) or in a separate collection connected by
a reference.

Embed when the relationship is one-to-few, when the child data is almost
always read together with the parent, and when the child has no independent
lifecycle. A classic example is line items inside an order: they are created
with the order, read with the order, and never queried on their own. Embedding
also gives atomic updates across the parent and its children in a single write.

Reference when the relationship is one-to-many or many-to-many, when the child
data is shared between parents, or when the child grows without bound. A
product catalog referenced by many orders should live in its own collection;
embedding it would duplicate it everywhere and make updates painful. Unbounded
arrays are an anti-pattern: a document that keeps growing eventually hurts
write performance and hits the 16 MB document size limit.

A useful heuristic is the subset pattern: embed only the most recent or most
relevant slice of a large relationship in the parent document (for example the
ten latest reviews) and keep the full set in its own collection, referenced by
the parent id.

Schema design in MongoDB follows the workload, not the entity diagram. Model
for the queries the application actually runs: data that is accessed together
should be stored together.
