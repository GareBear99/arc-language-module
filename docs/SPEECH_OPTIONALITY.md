# Speech Optionality

The speech layer is optional by design.

Reasons:
- not all environments have suitable hardware
- language truth must remain independent from audio synthesis
- text-only mode is required for auditing, testing, and low-resource deployments

Provider states:
- disabled
- dry-run
- active

Supported provider boundary in this package:
- PersonaPlexAdapter (stub / optional dependency boundary)
