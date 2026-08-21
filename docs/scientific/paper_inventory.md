# G3 Adult Drosophila Parkinson Locomotion Paper Inventory

This inventory expands the adult locomotion literature context without changing
the frozen E4 matrix or any simulation evidence. Mappings are repository
coverage statements only. They do not validate a Parkinson's disease model.

## Included Papers

| ID | Paper | Adult PD locomotion evidence | Repository coverage |
| --- | --- | --- | --- |
| `riemensperger_2011_dopamine_deficiency` | Riemensperger et al. 2011, PNAS. DOI: [10.1073/pnas.1010930108](https://doi.org/10.1073/pnas.1010930108), PMID: 21187381. | Neural dopamine-deficient adult flies showed decreased walking speed and covered distance; negative geotaxis/climbing was also impaired. | Speed is `SUPPORTED`; distance is `PARTIALLY_SUPPORTED`; climbing/SING is `NOT_SUPPORTED`. |
| `chen_2014_a30p_walking` | Chen et al. 2014, Genes, Brain and Behavior. DOI: [10.1111/gbb.12172](https://doi.org/10.1111/gbb.12172), PMID: 25113870. | Old adult A30P flies had decreased total moving distance, distance per movement, velocity, angular velocity, and increased centrophobism. | Velocity is `SUPPORTED`; total distance is `PARTIALLY_SUPPORTED`; bout distance, angular velocity, and centrophobism are `NOT_SUPPORTED`. |
| `riemensperger_2013_alpha_syn_dopamine_pathway` | Riemensperger et al. 2013, Cell Reports. DOI: [10.1016/j.celrep.2013.10.032](https://doi.org/10.1016/j.celrep.2013.10.032), PMID: 24239353. | Human alpha-synuclein in all neurons or selected PAM dopamine neurons produced progressive locomotor/climbing deficits in adult flies. | SING/climbing endpoints are `NOT_SUPPORTED` by current flat-ground metrics. |
| `aggarwal_2019_automated_climbing` | Aggarwal et al. 2019, PNAS. DOI: [10.1073/pnas.1807456116](https://doi.org/10.1073/pnas.1807456116), PMID: 31748267. | Automated adult climbing behavior revealed locomotor defects in heterozygous fly Parkinson-gene contexts. | Automated climbing parameters are `NOT_SUPPORTED`. |
| `liu_2008_lrrk2_parkinsonism` | Liu et al. 2008, PNAS. DOI: [10.1073/pnas.0708452105](https://doi.org/10.1073/pnas.0708452105), PMID: 18258746. | Human LRRK2 or LRRK2-G2019S expression caused adult-onset locomotor dysfunction, climbing deficits, actometer changes, and L-DOPA-responsive locomotor impairment. | Actometer activity is `PARTIALLY_SUPPORTED` at most; climbing and L-DOPA behavior are `NOT_SUPPORTED`. |
| `cording_2017_lrrk2_per` | Cording et al. 2017, NPJ Parkinson's Disease. DOI: [10.1038/s41531-017-0036-y](https://doi.org/10.1038/s41531-017-0036-y), PMID: 29214211. | LRRK2 mutations in dopaminergic neurons slowed proboscis extension, increased duration variability, and increased tremor. | PER and tremor endpoints are `NOT_SUPPORTED`. |
| `coulom_2004_rotenone` | Coulom and Birman 2004, Journal of Neuroscience. DOI: [10.1523/JNEUROSCI.2993-04.2004](https://doi.org/10.1523/JNEUROSCI.2993-04.2004), PMID: 15574749. | Chronic rotenone exposure in adults produced dose-dependent negative-geotaxis locomotor impairments and L-DOPA-responsive behavioral deficits. | Rotenone/SING and biological L-DOPA rescue are `NOT_SUPPORTED`. |
| `park_2005_dj1` | Park et al. 2005, Gene. DOI: [10.1016/j.gene.2005.06.040](https://doi.org/10.1016/j.gene.2005.06.040), PMID: 16203113. | Homozygous DJ-1 mutants showed oxidative-stress-sensitive locomotive dysfunction. | Current mapping is `NOT_SUPPORTED` because the accessible endpoint wording is too broad for the present metric set. |
| `poddighe_2014_pink1b9_mucuna` | Poddighe et al. 2014, PLOS ONE. DOI: [10.1371/journal.pone.0110802](https://doi.org/10.1371/journal.pone.0110802), PMID: 25340511. | PINK1B9 adults at 3-6, 10-15, and 20-25 days were assessed for climbing; treatment improved climbing behavior. | Biological treatment/rescue climbing is `NOT_SUPPORTED`. Confidence is `LIMITED` because an expression of concern exists. |
| `kajtor_2025_trial_based_behavior` | Kajtor et al. 2025, eLife. DOI: [10.7554/eLife.90905.3](https://doi.org/10.7554/eLife.90905.3), PMID: not found in PubMed search on 2026-08-12. | Adult Parkin-R275W flies showed reduced walking speed and lower reactivity; alpha-synuclein A53T flies showed increased stop durations in a passing-shadow assay. | Mean speed is `PARTIALLY_SUPPORTED`; stop/freezing and reactivity are `NOT_SUPPORTED`. |

## Reviewed But Excluded From Mapped Adult Locomotion Evidence

| Paper | Reason |
| --- | --- |
| Vincent et al. 2012, Human Molecular Genetics, DOI: [10.1093/hmg/ddr609](https://doi.org/10.1093/hmg/ddr609), PMID: 22215442. | Larval parkin locomotion; excluded by adult-only scope. |
| Julienne et al. 2017, Neurobiology of Disease, DOI: [10.1016/j.nbd.2017.04.014](https://doi.org/10.1016/j.nbd.2017.04.014), PMID: 28435104. | Primarily non-motor memory/circadian endpoints; not mapped as adult locomotion phenotype evidence. |

## Notes

- `SUPPORTED` means a current repository observable is a close qualitative
  counterpart, not a calibrated biological measurement.
- `PARTIALLY_SUPPORTED` means the repository has a related observable but the
  assay context or metric definition differs materially.
- `NOT_SUPPORTED` means current frozen evidence does not measure the endpoint.
