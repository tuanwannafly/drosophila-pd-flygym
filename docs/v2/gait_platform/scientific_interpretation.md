# Scientific Interpretation

The gait platform quantifies computational behavior in simulated rollouts. It
does not establish biological validation or Parkinson's disease status.

## Implemented Descriptors

- Stride events and timing describe repeated contact onsets in the simulated
  contact state.
- Stance and swing bouts describe binary support phases inferred from contact
  or adhesion arrays.
- Duty factor summarizes the fraction of samples in contact.
- Coordination matrices and cross correlations summarize contact coactivity.
- Inter-leg phase and phase locking summarize relative contact-onset timing.
- Tripod and tetrapod scores summarize canonical six-leg support patterns.
- Gait entropy and transition counts summarize support-pattern variability.

## Interpretation Boundary

These measurements can support computational comparisons such as unperturbed
versus perturbed rollouts when simulations are generated elsewhere under a
controlled protocol. They do not by themselves imply dopamine depletion,
neuron loss, disease severity, biological rescue, mechanistic equivalence, or
statistical significance.

## Future Evidence Needs

Biological interpretation requires explicit mapping to peer-reviewed adult
Drosophila endpoints, experimental assay comparability, and an authorized
validation layer separate from this measurement implementation.
