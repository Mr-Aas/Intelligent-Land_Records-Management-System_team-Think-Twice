"""
stage3 — Cadastral / Bhu-Naksha Validation.

Evaluates municipally-matched structures against cadastral land parcels.
Determines primary parcel (major part of structure by area) and checks for
boundary overflow against a configurable distance threshold.
Classifies records into verified, audit_pending, and disputed.
"""
