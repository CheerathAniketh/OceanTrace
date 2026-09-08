// Single source of truth for risk color/label, shared across
// VesselRanking and DossierPanel so a vessel's color never
// disagrees with itself depending on which view you're looking at.
export function riskTier(scorePct) {
  if (scorePct > 70) return { label: 'high-risk', color: 'var(--accent-red)' };
  if (scorePct > 40) return { label: 'med-risk', color: 'var(--accent-orange, #f59e0b)' };
  return { label: 'low-risk', color: 'var(--accent-green, #22c55e)' };
}