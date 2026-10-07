import re
import unicodedata

# Philippine regions and the provinces/states that belong to each one.
PH_REGIONS = {
    ('NCR', 'National Capital Region (NCR)'): [
        'metro manila', 'national capital region', 'ncr', 'manila',
    ],
    ('CAR', 'Cordillera Administrative Region (CAR)'): [
        'abra', 'apayao', 'benguet', 'ifugao', 'kalinga', 'mountain province',
    ],
    ('I', 'Ilocos Region (Region I)'): [
        'ilocos norte', 'ilocos sur', 'la union', 'pangasinan',
    ],
    ('II', 'Cagayan Valley (Region II)'): [
        'batanes', 'cagayan', 'isabela', 'nueva vizcaya', 'quirino',
    ],
    ('III', 'Central Luzon (Region III)'): [
        'aurora', 'bataan', 'bulacan', 'nueva ecija', 'pampanga', 'tarlac', 'zambales',
    ],
    ('IV-A', 'CALABARZON (Region IV-A)'): [
        'batangas', 'cavite', 'laguna', 'quezon', 'rizal',
    ],
    ('IV-B', 'MIMAROPA (Region IV-B)'): [
        'marinduque', 'occidental mindoro', 'oriental mindoro', 'palawan', 'romblon',
    ],
    ('V', 'Bicol Region (Region V)'): [
        'albay', 'camarines norte', 'camarines sur', 'catanduanes', 'masbate', 'sorsogon',
    ],
    ('VI', 'Western Visayas (Region VI)'): [
        'aklan', 'antique', 'capiz', 'guimaras', 'iloilo', 'negros occidental',
    ],
    ('VII', 'Central Visayas (Region VII)'): [
        'bohol', 'cebu', 'negros oriental', 'siquijor',
    ],
    ('VIII', 'Eastern Visayas (Region VIII)'): [
        'biliran', 'eastern samar', 'leyte', 'northern samar', 'samar', 'southern leyte',
    ],
    ('IX', 'Zamboanga Peninsula (Region IX)'): [
        'zamboanga del norte', 'zamboanga del sur', 'zamboanga sibugay',
    ],
    ('X', 'Northern Mindanao (Region X)'): [
        'bukidnon', 'camiguin', 'lanao del norte', 'misamis occidental', 'misamis oriental',
    ],
    ('XI', 'Davao Region (Region XI)'): [
        'davao de oro', 'compostela valley', 'davao del norte', 'davao del sur',
        'davao occidental', 'davao oriental',
    ],
    ('XII', 'SOCCSKSARGEN (Region XII)'): [
        'cotabato', 'sarangani', 'south cotabato', 'sultan kudarat',
    ],
    ('XIII', 'Caraga (Region XIII)'): [
        'agusan del norte', 'agusan del sur', 'dinagat islands', 'surigao del norte',
        'surigao del sur',
    ],
    ('BARMM', 'Bangsamoro Autonomous Region in Muslim Mindanao (BARMM)'): [
        'basilan', 'lanao del sur', 'maguindanao', 'sulu', 'tawi-tawi', 'tawi tawi',
    ],
}


def _norm(text):
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text).split())


def _post_init_link_regions(env):
    """Create the Philippine regions and link the existing states to them."""
    country = env.ref('base.ph', raise_if_not_found=False)
    if not country:
        return
    Region = env['res.country.region']
    states = env['res.country.state'].search([('country_id', '=', country.id)])
    state_names = {state: _norm(state.name) for state in states}

    for (code, name), keywords in PH_REGIONS.items():
        region = Region.search([('country_id', '=', country.id), ('code', '=', code)], limit=1)
        if not region:
            region = Region.create({'name': name, 'code': code, 'country_id': country.id})
        wanted = {_norm(k) for k in keywords}
        for state, state_name in state_names.items():
            if not state.region_id and state_name in wanted:
                state.region_id = region
