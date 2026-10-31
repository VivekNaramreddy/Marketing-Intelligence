def generate_findings(metrics):
    findings = []
    for p in metrics['platforms']:
        kind, title, summary = None, '', ''
        if p['engagement_difference'] is not None and p['competitor_engagement_rate'] > 0 and p['engagement_difference'] / p['competitor_engagement_rate'] <= -0.2:
            kind, title = 'Weakness', f"{p['platform']} engagement gap"
            summary = f"Engagement is {p['engagement_rate']:.2f}% versus a {p['competitor_engagement_rate']:.2f}% selected-competitor average ({p['engagement_difference']:.2f} percentage points)."
        elif p['rank'] == 1 and p['followers'] > p['competitor_average']:
            kind, title = 'Strength', f"{p['platform']} audience lead"
            summary = f"Audience ranks first among {p['compared_brands']} brands with available follower counts."
        elif p['followers'] is not None and p['followers'] > 0 and p['peer_count'] == 0:
            kind, title = 'Opportunity', f"Explore {p['platform']} presence"
            summary = 'Your brand has a measured audience; selected competitors have no comparable follower values in the imported data. This does not establish that they have no presence.'
        if kind:
            findings.append({'type': kind, 'title': title, 'summary': summary, 'evidence': p, 'source_metrics': p['source_ids'], 'confidence': 'Limited' if not p['peer_count'] or len(p['dates']) > 1 else 'Moderate', 'recommendation': 'Review the content behind the engagement gap and test one focused improvement.' if kind == 'Weakness' else 'Validate coverage and reporting dates before using this comparison to guide investment.'})
    return sorted(findings, key=lambda f: {'Weakness': 0, 'Strength': 1, 'Opportunity': 2}[f['type']])[:5]
