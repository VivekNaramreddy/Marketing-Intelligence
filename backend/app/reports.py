def build_report(primary, metrics, findings):
    audience = f"{metrics['audience']:,.0f}" if metrics['audience'] is not None else 'unavailable'
    return {'title': f'{primary} · Basic intelligence report', 'sections': [
        {'title': 'Executive Summary', 'items': [f'Available audience totals {audience} followers across {metrics["coverage"]["follower_platforms"]} measured platforms. Audiences may overlap.', f'{len(findings)} rules-based findings were identified from the selected comparison.']},
        {'title': 'Competitive Overview', 'items': [f"{p['platform']}: rank {p['rank']} of {p['compared_brands']} measured brands." for p in metrics['platforms'] if p['rank'] is not None] or ['No comparable follower observations available.']},
        {'title': 'Strengths', 'items': [f['summary'] for f in findings if f['type'] == 'Strength'] or ['No strength rule triggered by the available data.']},
        {'title': 'Areas for Improvement', 'items': [f['summary'] for f in findings if f['type'] == 'Weakness'] or ['No engagement-gap rule triggered by the available data.']},
        {'title': 'Recommendations', 'items': list(dict.fromkeys(f['recommendation'] for f in findings)) or ['Import comparable competitor observations to expand the analysis.']},
    ], 'findings': findings, 'methodology': metrics['methodology']}
