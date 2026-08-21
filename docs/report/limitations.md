# Limitations

## Biological interpretation

- The motor-vigor and coordination variables are computational proxies, not
  measurements of dopamine, neuron loss, synaptic failure, or disease stage.
- No parameter value is designated as Parkinson's disease, dopamine depletion,
  neuron-loss percentage, biological severity, or mechanistic disease state.
- No pharmacological intervention or L-DOPA response is simulated.
- E5 reports computational reversibility only. It is not biological rescue,
  treatment response, or recovery of a real fly.
- E4 is a selected, qualitative literature comparison and remains
  `PARTIAL_PHENOTYPE_CONCORDANCE`; it is not a validation score.

## Measurement and model limitations

- Simulated displacement, speed, path length, yaw, action magnitude, and body
  height are outputs of the configured model and controller.
- Yaw change is an angular displacement over the run, not angular velocity.
- Body height changes substantially under some perturbations and may confound
  interpretation of locomotor output.
- The response surfaces are not evidence that the chosen proxies are
  biologically comparable across parameter scales.
- The short baseline and paired runs characterize the tested protocol, not all
  timescales or environmental conditions.
- The report does not introduce biological acceptance thresholds.

## Robustness and inference

- E3 tested five paired seeds, `[0, 1, 2, 3, 4]`, for one frozen candidate.
- The `ROBUST` label means computational/software robustness under those tested
  seeds only. It does not mean biological robustness or statistical
  significance.
- The frozen evidence contains no inferential statistical significance claim.
- Seed replication does not replace independent experimental validation or a
  prespecified biological analysis.

## Reproducibility and scope

- The simulation stack is version-sensitive and tied to the documented Python,
  FlyGym, and MuJoCo versions.
- Upstream simulation reports require the pinned Colab environment; the E6
  evidence synthesis itself is evidence-only and can run without rerunning
  FlyGym/MuJoCo.
- Historical notebooks may contain exploratory or debugging cells and are not
  the canonical implementation.
- The known dirty Session 02 notebook was preserved outside the E6 synthesis
  scope. Its dirty-worktree flag is provenance information, not a result.
