# Desktop host

`main.py` delegates to the same entry point as `python -m chess_and_chains`.
See the [quick start](../README.md#quick-start-for-contributors) for source
and installed use. The Tk host lives in [`src/chess_and_chains/ui/`](../src/chess_and_chains/ui/).
Chess rules live separately in [`src/chess_and_chains/chess/`](../src/chess_and_chains/chess/).
The [Glide Shell integration gate](../integrations/glide_shell/INTEGRATION_GATE.md) describes the reuse decision.
